#!/bin/bash
set -euo pipefail
ACTION="$HOME/Library/Services/Prepare Debug Bundle.workflow"
APP="$HOME/.local/share/prepare-debug-bundle"
if [[ -e "$ACTION" ]]; then
  ID="$(/usr/libexec/PlistBuddy -c 'Print :CFBundleIdentifier' "$ACTION/Contents/Info.plist" 2>/dev/null || true)"
  [[ "$ID" == 'dev.chizh.prepare-debug-bundle' ]] || { echo 'Refusing to remove an unrelated Finder action.' >&2; exit 1; }
  rm -rf -- "$ACTION"
fi
rm -f -- "$APP/bundle.py" "$APP/run.sh"
rmdir "$APP" 2>/dev/null || true
if [[ -x /System/Library/CoreServices/pbs ]]; then
  /System/Library/CoreServices/pbs -update >/dev/null 2>&1 || true
fi
echo 'Removed Quick Action and installed scripts.'
echo "Kept your settings (~/.config/prepare-debug-bundle/) and generated ZIPs."
