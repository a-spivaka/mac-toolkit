#!/bin/bash
set -euo pipefail
ROOT="$(cd -- "$(dirname -- "$0")" && pwd)"
SHARE="$HOME/.local/share/git-finder-actions"
SERVICES="$HOME/Library/Services"
[[ "$(uname -s)" == 'Darwin' ]] || { echo 'This package must be installed on macOS.' >&2; exit 1; }
command -v git >/dev/null 2>&1 || { echo 'Git must be installed.' >&2; exit 1; }
found_python=0
for candidate in /opt/homebrew/bin/python3 /usr/local/bin/python3 /usr/bin/python3; do
  if [[ -x "$candidate" ]] && "$candidate" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)' >/dev/null 2>&1; then
    found_python=1
    break
  fi
done
[[ $found_python -eq 1 ]] || { echo 'Python 3.8+ is required.' >&2; exit 1; }
NAMES=('Git - Show Status' 'Git - Copy Working Diff' 'Git - Open PR' 'Git - Copy Context')
IDS=('dev.chizh.git-finder-actions.status' 'dev.chizh.git-finder-actions.diff' 'dev.chizh.git-finder-actions.open-pr' 'dev.chizh.git-finder-actions.context')
for index in "${!NAMES[@]}"; do
  name="${NAMES[$index]}"
  source="$ROOT/$name.workflow"
  target="$SERVICES/$name.workflow"
  [[ -f "$source/Contents/document.wflow" ]] || { echo "Missing $source" >&2; exit 1; }
  if [[ -e "$target" ]]; then
    existing="$(/usr/libexec/PlistBuddy -c 'Print :CFBundleIdentifier' "$target/Contents/Info.plist" 2>/dev/null || true)"
    [[ "$existing" == "${IDS[$index]}" ]] || { echo "Refusing to replace unrelated workflow: $target" >&2; exit 1; }
  fi
done
mkdir -p "$SHARE" "$SERVICES"
install -m 755 "$ROOT/git_actions.py" "$SHARE/git_actions.py"
install -m 755 "$ROOT/run.sh" "$SHARE/run.sh"
for name in "${NAMES[@]}"; do
  target="$SERVICES/$name.workflow"
  if [[ -d "$target" ]]; then rm -rf -- "$target"; fi
  cp -R "$ROOT/$name.workflow" "$target"
done
if [[ -x /System/Library/CoreServices/pbs ]]; then /System/Library/CoreServices/pbs -update >/dev/null 2>&1 || true; fi
cat <<'MESSAGE'
Git Finder Actions installed. In Finder, right-click a repository folder or a file inside it:
  Quick Actions > Git - Show Status
  Quick Actions > Git - Copy Working Diff
  Quick Actions > Git - Open PR
  Quick Actions > Git - Copy Context

The actions do not perform fetch, push, merge, reset, or change repository files.
For PR lookup, GitHub CLI (gh) is optional; without it, a branch-filtered PR list opens.
You may delete the extracted installer folder after installation.
MESSAGE
