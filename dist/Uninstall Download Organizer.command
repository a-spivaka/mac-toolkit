#!/bin/bash
set -u
cd "$(dirname "$0")" || exit 1
echo "Uninstalling Download Organizer for this Mac user..."
if bash "./download-organizer/uninstall.sh"; then
  echo "Download Organizer was stopped and uninstalled."
  echo "Your downloaded files and settings were preserved."
else
  echo "Uninstall failed. Review the error above."
fi
echo
read -r -p "Press Return to close this window..." _
