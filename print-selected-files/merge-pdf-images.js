/*
 * Print Selected Files — native PDFKit merger for macOS JavaScript for Automation.
 * Usage: osascript -l JavaScript merge-pdf-images.js output.pdf input1 input2 ...
 * Requires no third-party libraries or compiler.
 */
ObjC.import('Foundation');
ObjC.import('AppKit');
ObjC.import('PDFKit');

function leafName(path) {
    var parts = path.split('/');
    return parts[parts.length - 1];
}

function sortedPaths(paths) {
    return paths.slice().sort(function(a, b) {
        // Sort based on filename; numbered prefixes such as 01 / 02 control order.
        var cmp = leafName(a).localeCompare(leafName(b), undefined, {
            numeric: true,
            sensitivity: 'base'
        });
        return cmp || a.localeCompare(b);
    });
}

function fileExtension(path) {
    var name = leafName(path);
    var dot = name.lastIndexOf('.');
    return dot < 0 ? '' : name.substring(dot).toLowerCase();
}

function run(argv) {
    if (argv.length < 2) {
        throw new Error('Select one or more PDF or image files.');
    }

    var destinationPath = String(argv[0]);
    var ordered = sortedPaths(argv.slice(1).map(String));
    var merged = $.PDFDocument.alloc.init;
    var sources = []; // Keep source PDFDocuments alive through the final write.
    var supportedImages = {
        '.png': true, '.jpg': true, '.jpeg': true, '.heic': true,
        '.heif': true, '.tif': true, '.tiff': true, '.bmp': true, '.gif': true
    };

    for (var i = 0; i < ordered.length; i++) {
        var path = ordered[i];
        var url = $.NSURL.fileURLWithPath($(path));
        var ext = fileExtension(path);

        if (ext === '.pdf') {
            var src = $.PDFDocument.alloc.initWithURL(url);
            if (!src) {
                throw new Error('Cannot open PDF: ' + leafName(path));
            }
            if (src.isLocked) {
                throw new Error('Password-protected PDF: ' + leafName(path));
            }
            var pages = Number(src.pageCount);
            if (!pages) {
                throw new Error('Empty or unreadable PDF: ' + leafName(path));
            }
            sources.push(src);
            for (var j = 0; j < pages; j++) {
                var sourcePage = src.pageAtIndex(j);
                if (!sourcePage) {
                    throw new Error('Cannot read page ' + (j + 1) + ' in ' + leafName(path));
                }
                merged.insertPageAtIndex(sourcePage, Number(merged.pageCount));
            }
        } else if (supportedImages[ext]) {
            var nsImage = $.NSImage.alloc.initWithContentsOfURL(url);
            if (!nsImage) {
                throw new Error('Cannot load image: ' + leafName(path));
            }
            var page = $.PDFPage.alloc.initWithImage(nsImage);
            if (!page) {
                throw new Error('Cannot convert image: ' + leafName(path));
            }
            merged.insertPageAtIndex(page, Number(merged.pageCount));
        } else {
            throw new Error('Unsupported file type: ' + leafName(path));
        }
    }

    if (Number(merged.pageCount) === 0) {
        throw new Error('No printable pages found.');
    }
    var targetURL = $.NSURL.fileURLWithPath($(destinationPath));
    if (!merged.writeToURL(targetURL)) {
        throw new Error('Could not write merged PDF.');
    }
    return String(merged.pageCount) + ' pages merged from ' + ordered.length + ' files';
}
