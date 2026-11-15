#!/bin/bash
# Update an existing Finder Quick Action's script without modifying the workflow.
set -euo pipefail
ROOT="$(cd -- "$(dirname -- "$0")" && pwd)"
DEST="$HOME/.local/share/open-dev-workspace/open-workspace.sh"
if [[ "$(uname -s)" != "Darwin" ]]; then
  echo "This update is for macOS only." >&2
  exit 1
fi
if [[ ! -f "$DEST" || -L "$DEST" ]]; then
  echo "Existing Open Development Workspace installation not found: $DEST" >&2
  echo "Install the original Quick Action first." >&2
  exit 1
fi
install -m 755 "$ROOT/open-workspace.sh" "$DEST"
echo "Updated: $DEST"
echo "Try the Finder Quick Action again. No reinstall or restart needed."
