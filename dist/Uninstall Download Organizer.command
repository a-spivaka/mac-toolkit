#!/bin/bash
set -u
cd "$(dirname "$0")" || exit 1
echo "Uninstalling Download Organizer for $(id -un)..."
if bash "./download-organizer/uninstall.sh"; then
  echo "Download Organizer removed. Python is NOT uninstalled."
  echo "Downloads, settings, and logs are preserved."
else
  echo "Uninstall failed. See the error above."
fi
echo
read -r -p "Press Return to close this window..." _ || true
