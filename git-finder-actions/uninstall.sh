#!/bin/bash
set -euo pipefail
SERVICES="$HOME/Library/Services"
NAMES=('Git - Show Status' 'Git - Copy Working Diff' 'Git - Open PR' 'Git - Copy Context')
IDS=('dev.chizh.git-finder-actions.status' 'dev.chizh.git-finder-actions.diff' 'dev.chizh.git-finder-actions.open-pr' 'dev.chizh.git-finder-actions.context')
for index in "${!NAMES[@]}"; do
  target="$SERVICES/${NAMES[$index]}.workflow"
  if [[ -d "$target" ]]; then
    existing="$(/usr/libexec/PlistBuddy -c 'Print :CFBundleIdentifier' "$target/Contents/Info.plist" 2>/dev/null || true)"
    if [[ "$existing" == "${IDS[$index]}" ]]; then rm -rf -- "$target"; else echo "Not our workflow: $target" >&2; fi
  fi
done
rm -f -- "$HOME/.local/share/git-finder-actions/git_actions.py" "$HOME/.local/share/git-finder-actions/run.sh"
rmdir "$HOME/.local/share/git-finder-actions" 2>/dev/null || true
if [[ -x /System/Library/CoreServices/pbs ]]; then /System/Library/CoreServices/pbs -update >/dev/null 2>&1 || true; fi
echo 'Git Finder Actions removed.'
