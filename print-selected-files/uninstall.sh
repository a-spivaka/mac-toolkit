#!/bin/bash
set -euo pipefail
SERVICES_DIR="$HOME/Library/Services"
APP_DIR="$HOME/Library/Application Support/Print Selected Files"
for name in 'Print Selected Files' 'Preview Selected Files'; do
  workflow="$SERVICES_DIR/$name.workflow"
  if [[ -d "$workflow" ]]; then /bin/rm -rf -- "$workflow"; fi
done
if [[ -d "$APP_DIR" ]]; then /bin/rm -rf -- "$APP_DIR"; fi
/System/Library/CoreServices/pbs -flush >/dev/null 2>&1 || true
echo 'Print Selected Files and Preview Selected Files have been uninstalled.'
echo 'Temporary combined PDFs can be removed from ~/Library/Caches/Print Selected Files.'
