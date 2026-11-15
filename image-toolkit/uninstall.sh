#!/bin/bash
set -euo pipefail
SERVICES="$HOME/Library/Services"
NAMES=('Image - Convert to JPEG' 'Image - Convert to PNG' 'Image - Resize to 1600px' 'Image - Web JPEG 1600px')
IDS=('dev.chizh.image-toolkit.jpeg' 'dev.chizh.image-toolkit.png' 'dev.chizh.image-toolkit.resize1600' 'dev.chizh.image-toolkit.web1600')
for index in "${!NAMES[@]}"; do
  target="$SERVICES/${NAMES[$index]}.workflow"
  if [[ -d "$target" ]]; then
    existing="$(/usr/libexec/PlistBuddy -c 'Print :CFBundleIdentifier' "$target/Contents/Info.plist" 2>/dev/null || true)"
    if [[ "$existing" == "${IDS[$index]}" ]]; then rm -rf -- "$target"; else echo "Not our workflow, leaving intact: $target" >&2; fi
  fi
done
rm -f -- "$HOME/.local/share/image-toolkit/image-toolkit.sh"
rmdir "$HOME/.local/share/image-toolkit" 2>/dev/null || true
if [[ -x /System/Library/CoreServices/pbs ]]; then /System/Library/CoreServices/pbs -update >/dev/null 2>&1 || true; fi
echo 'Image Toolkit removed.'
