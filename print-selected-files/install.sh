#!/bin/bash
set -euo pipefail
if [[ "$(/usr/bin/uname -s)" != 'Darwin' ]]; then
  echo 'This installer runs on macOS only.' >&2
  exit 1
fi
SRC="$(cd "$(dirname "$0")" && pwd)"
APP_DIR="$HOME/Library/Application Support/Print Selected Files"
SERVICES_DIR="$HOME/Library/Services"
/bin/mkdir -p "$APP_DIR" "$SERVICES_DIR"
/usr/bin/install -m 755 "$SRC/print-selected-files.sh" "$APP_DIR/print-selected-files.sh"
/usr/bin/install -m 644 "$SRC/merge-pdf-images.js" "$APP_DIR/merge-pdf-images.js"
for NAME in 'Print Selected Files' 'Preview Selected Files'; do
  WORKFLOW="$SERVICES_DIR/$NAME.workflow"
  /bin/mkdir -p "$WORKFLOW/Contents"
  /usr/bin/install -m 644 "$SRC/$NAME.workflow/Contents/Info.plist" "$WORKFLOW/Contents/Info.plist"
  /usr/bin/install -m 644 "$SRC/$NAME.workflow/Contents/document.wflow" "$WORKFLOW/Contents/document.wflow"
done
/System/Library/CoreServices/pbs -flush >/dev/null 2>&1 || true
printf '\nInstalled Finder Quick Actions:\n'
printf '  Print Selected Files   -> submits one merged job to the default printer\n'
printf '  Preview Selected Files -> opens the merged PDF in Preview; does not print\n'
