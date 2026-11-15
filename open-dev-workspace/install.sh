#!/bin/bash
set -euo pipefail

ROOT="$(cd -- "$(dirname -- "$0")" && pwd)"
SOURCE="$ROOT/Open Development Workspace.workflow"
INSTALL_ROOT="$HOME/.local/share/open-dev-workspace"
SERVICES="$HOME/Library/Services"
DEST="$SERVICES/Open Development Workspace.workflow"

[[ "$(uname -s)" == "Darwin" ]] || { echo 'This installer works only on macOS.' >&2; exit 1; }
[[ -f "$SOURCE/Contents/document.wflow" ]] || { echo 'Workflow bundle missing. Extract the complete ZIP first.' >&2; exit 1; }
if [[ -e "$DEST" ]]; then
  echo "A Quick Action already exists at: $DEST" >&2
  echo 'Please use uninstall.sh first if you want to replace this installation.' >&2
  exit 1
fi
mkdir -p "$INSTALL_ROOT" "$SERVICES"
install -m 755 "$ROOT/open-workspace.sh" "$INSTALL_ROOT/open-workspace.sh"
cp -R "$SOURCE" "$DEST"
chmod 644 "$DEST/Contents/Info.plist" "$DEST/Contents/document.wflow"
# Ask the macOS Services database to discover this workflow; don't force-close Finder.
if [[ -x /System/Library/CoreServices/pbs ]]; then
  /System/Library/CoreServices/pbs -update >/dev/null 2>&1 || true
fi
cat <<END
Installed:
  Script:       $INSTALL_ROOT/open-workspace.sh
  Quick Action: $DEST

Finder → right-click a repository folder → Quick Actions → Open Development Workspace

Test without opening applications:
  "$INSTALL_ROOT/open-workspace.sh" --dry-run "$HOME"
  (For an actual result, replace "$HOME" with the path of a Git repository.)

If it does not show up immediately, open Finder → Quick Actions → Customize,
or check System Settings → Keyboard → Keyboard Shortcuts → Services.
END
