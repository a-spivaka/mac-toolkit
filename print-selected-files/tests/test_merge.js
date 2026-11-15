const assert = require('assert');
const fs = require('fs');
const vm = require('vm');
const path = require('path');

const code = fs.readFileSync(path.join(__dirname, '..', 'merge-pdf-images.js'), 'utf8');
function mockRun(args, fixture) {
  const pages = [];
  const seen = [];
  const failImages = fixture.failImages || {};
  const pdfs = fixture.pdfs || {};
  const images = fixture.images || {};
  const state = { wrote: false, destination: null };
  const doc = {
    get pageCount() { return pages.length; },
    insertPageAtIndex(page, index) { assert.strictEqual(index, pages.length); pages.push(page); },
    writeToURL(url) { state.wrote = true; state.destination = url; return fixture.writeFails ? false : true; }
  };
  const dollar = function(a) { return String(a); };
  dollar.PDFDocument = { alloc: {
    init: doc,
    initWithURL(url) {
      seen.push(url);
      const spec = pdfs[url];
      if (!spec) return null;
      return {
        isLocked: !!spec.locked,
        pageCount: spec.pages,
        pageAtIndex(i) { return url + '-page-' + i; }
      };
    }
  } };
  dollar.PDFPage = { alloc: {initWithImage(img) {return img + '-page';}} };
  dollar.NSImage = {alloc: {initWithContentsOfURL(url) {return failImages[url] ? null : (images[url] ? url : null);}}};
  dollar.NSURL = {fileURLWithPath(s) {return s;}};
  const context = {ObjC: {import() {}}, $: dollar};
  vm.createContext(context);
  vm.runInContext(code, context);
  const result = context.run(args);
  return {pages, seen, state, result};
}
const batch=mockRun(['/tmp/all.pdf','/tmp/10.pdf','/tmp/2.jpg','/tmp/1.pdf'], {
  pdfs:{'/tmp/1.pdf':{pages:2},'/tmp/10.pdf':{pages:1}},
  images:{'/tmp/2.jpg':true}
});
assert.deepStrictEqual(batch.pages, ['/tmp/1.pdf-page-0','/tmp/1.pdf-page-1','/tmp/2.jpg-page','/tmp/10.pdf-page-0']);
assert.strictEqual(batch.state.wrote,true);
assert.strictEqual(batch.result,'4 pages merged from 3 files');
assert.throws(()=>mockRun(['/tmp/out.pdf','/tmp/locked.pdf'],{pdfs:{'/tmp/locked.pdf':{pages:1,locked:true}}}), /Password-protected/);
assert.throws(()=>mockRun(['/tmp/out.pdf','/tmp/file.docx'],{}),/Unsupported file type/);
assert.throws(()=>mockRun(['/tmp/out.pdf','/tmp/empty.pdf'],{pdfs:{'/tmp/empty.pdf':{pages:0}}}),/Empty or unreadable/);
assert.throws(()=>mockRun(['/tmp/out.pdf','/tmp/bad.PNG'],{failImages:{'/tmp/bad.PNG':true}}),/Cannot load image/);
assert.throws(()=>mockRun(['/tmp/out.pdf','/tmp/1.png'],{images:{'/tmp/1.png':true},writeFails:true}),/Could not write/);
assert.throws(()=>mockRun(['/tmp/out.pdf'],{}), /Select one/);
console.log('7 JXA mocked PDFKit scenarios passed');
