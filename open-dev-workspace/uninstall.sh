#!/bin/bash
set -euo pipefail
DEST="$HOME/Library/Services/Open Development Workspace.workflow"
SCRIPT_DIR="$HOME/.local/share/open-dev-workspace"
if [[ -d "$DEST" ]]; then
  # Never remove an unrelated workflow that happens to share the name.
  id="$(/usr/libexec/PlistBuddy -c 'Print :CFBundleIdentifier' "$DEST/Contents/Info.plist" 2>/dev/null || true)"
  if [[ "$id" != 'dev.chizh.open-development-workspace' ]]; then
    echo 'Found a workflow with this name, but its identifier differs. Leaving it unchanged.' >&2
    exit 1
  fi
  rm -rf "$DEST"
fi
if [[ -f "$SCRIPT_DIR/open-workspace.sh" ]]; then
  rm -f "$SCRIPT_DIR/open-workspace.sh"
  rmdir "$SCRIPT_DIR" 2>/dev/null || true
fi
if [[ -x /System/Library/CoreServices/pbs ]]; then
  /System/Library/CoreServices/pbs -update >/dev/null 2>&1 || true
fi
echo 'Open Development Workspace has been removed.'
