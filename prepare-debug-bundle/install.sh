#!/bin/bash
set -euo pipefail
ROOT="$(cd -- "$(dirname -- "$0")" && pwd)"
SHARE="$HOME/.local/share/prepare-debug-bundle"
CONF_DIR="$HOME/.config/prepare-debug-bundle"
SERVICES="$HOME/Library/Services"
ACTION="$SERVICES/Prepare Debug Bundle.workflow"
SOURCE="$ROOT/Prepare Debug Bundle.workflow"

[[ "$(uname -s)" == 'Darwin' ]] || { echo 'Install on macOS only.' >&2; exit 1; }
[[ -f "$SOURCE/Contents/document.wflow" ]] || { echo 'Missing workflow bundle. Extract the entire ZIP.' >&2; exit 1; }
if ! command -v python3 >/dev/null 2>&1 && [[ ! -x /opt/homebrew/bin/python3 && ! -x /usr/local/bin/python3 && ! -x /usr/bin/python3 ]]; then
  echo 'Python 3 is required but not found.' >&2; exit 1
fi
if [[ -e "$ACTION" ]]; then
  ID="$(/usr/libexec/PlistBuddy -c 'Print :CFBundleIdentifier' "$ACTION/Contents/Info.plist" 2>/dev/null || true)"
  [[ "$ID" == 'dev.chizh.prepare-debug-bundle' ]] || { echo "Refusing to replace a different Quick Action at $ACTION" >&2; exit 1; }
fi
mkdir -p "$SHARE" "$CONF_DIR" "$SERVICES"
install -m 755 "$ROOT/bundle.py" "$SHARE/bundle.py"
install -m 755 "$ROOT/run.sh" "$SHARE/run.sh"
if [[ ! -f "$CONF_DIR/config.json" ]]; then
  install -m 600 "$ROOT/config.json" "$CONF_DIR/config.json"
else
  echo "Keeping existing configuration: $CONF_DIR/config.json"
fi
# Build workflow in package, then copy it to Services. Existing package is safe to refresh.
if [[ -d "$ACTION" ]]; then
  rm -rf -- "$ACTION"
fi
cp -R "$SOURCE" "$ACTION"
chmod 644 "$ACTION/Contents/Info.plist" "$ACTION/Contents/document.wflow"
if [[ -x /System/Library/CoreServices/pbs ]]; then
  /System/Library/CoreServices/pbs -update >/dev/null 2>&1 || true
fi
cat <<OUT
Installed Prepare Debug Bundle:
  Quick Action: $ACTION
  Script:       $SHARE/bundle.py
  Configuration:$CONF_DIR/config.json

Select several files in Finder → right-click → Quick Actions → Prepare Debug Bundle
The resulting ZIP will appear in ~/Downloads/Debug-Bundles and be revealed in Finder.

To try it from Terminal:
  python3 "$SHARE/bundle.py" --dry-run "$HOME/Downloads/example.log"
  (replace example.log with an existing file)
OUT
