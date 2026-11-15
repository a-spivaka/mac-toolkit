#!/bin/bash
set -euo pipefail
LABEL="local.download-organizer"
PLIST="$HOME/Library/LaunchAgents/$LABEL.plist"
if [[ -f "$PLIST" ]]; then
  launchctl bootout "gui/$(id -u)" "$PLIST" 2>/dev/null || true
  rm "$PLIST"
fi
rm -f "$HOME/.local/share/download-organizer/download_organizer.py"
echo "Stopped and removed Download Organizer LaunchAgent."
echo "Your configuration, logs, state and downloaded files were preserved."
