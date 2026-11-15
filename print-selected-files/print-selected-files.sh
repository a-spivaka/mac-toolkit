#!/bin/bash
# Finder Quick Action backend: merge PDFs/images and submit to the default printer.
# Use --preview to open the merged PDF in Preview instead of printing.
set -euo pipefail

MODE=print
if [[ ${1:-} == '--preview' ]]; then
    MODE=preview
    shift
fi

APP_DIR="$HOME/Library/Application Support/Print Selected Files"
MERGER="$APP_DIR/merge-pdf-images.js"
CACHE="$HOME/Library/Caches/Print Selected Files"
LOG="$CACHE/last-error.log"

report_error() {
    local message="$1"
    printf 'Print Selected Files: %s\n' "$message" >&2
    # Keep user-visible text constant; do not interpolate filenames into AppleScript.
    /usr/bin/osascript -e 'display alert "Print Selected Files" message "The job could not be prepared or submitted. Check ~/Library/Caches/Print Selected Files/last-error.log and your default printer." as warning' >/dev/null 2>&1 || true
}

if [[ $# -eq 0 ]]; then
    report_error 'No files were selected.'
    exit 1
fi

if [[ ! -f "$MERGER" ]]; then
    report_error 'Merge script is missing. Please rerun update.sh or install.sh.'
    exit 1
fi

for item in "$@"; do
    if [[ ! -f "$item" ]]; then
        report_error "Not a regular file: $item"
        exit 1
    fi
    ext="${item##*.}"
    ext="$(printf '%s' "$ext" | /usr/bin/tr '[:upper:]' '[:lower:]')"
    case "$ext" in
        pdf|png|jpg|jpeg|heic|heif|tif|tiff|bmp|gif) ;;
        *) report_error "Unsupported extension: $item"; exit 1 ;;
    esac
done

/bin/mkdir -p "$CACHE"
/bin/chmod 700 "$CACHE" 2>/dev/null || true
WORK_DIR="$(/usr/bin/mktemp -d "$CACHE/job-XXXXXXXX")"
OUTPUT="$WORK_DIR/Print Selected Files.pdf"

if ! /usr/bin/osascript -l JavaScript "$MERGER" "$OUTPUT" "$@" 2>"$LOG"; then
    report_error "Unable to merge files. See $LOG"
    /bin/rm -rf -- "$WORK_DIR"
    exit 1
fi

if [[ ! -s "$OUTPUT" ]]; then
    printf 'Merged output is missing or empty: %s\n' "$OUTPUT" >"$LOG"
    report_error 'Merged PDF is empty.'
    /bin/rm -rf -- "$WORK_DIR"
    exit 1
fi

# Keep temporary PDFs: CUPS may be processing them and Preview may need them.
# Old jobs are removed on a future invocation, never during the current job.
/usr/bin/find "$CACHE" -mindepth 1 -maxdepth 1 -type d -name 'job-*' -mtime +7 -exec /bin/rm -rf -- {} + 2>/dev/null || true

if [[ "$MODE" == preview ]]; then
    /usr/bin/open -a Preview "$OUTPUT"
    exit 0
fi

# lp submits the already merged PDF as ONE job to CUPS's default printer.
# It does not show Print or Save dialogs. Physical printing may still be delayed
# (printer offline, paper out, queue paused, etc.).
if ! /usr/bin/lp -t 'Print Selected Files' -- "$OUTPUT" >"$WORK_DIR/print-receipt.txt" 2>"$LOG"; then
    report_error 'Unable to queue print job. Check the default printer in System Settings -> Printers & Scanners.'
    exit 1
fi

cat "$WORK_DIR/print-receipt.txt"
/usr/bin/osascript -e 'display notification "Combined PDF sent to the default printer." with title "Print Selected Files"' >/dev/null 2>&1 || true
