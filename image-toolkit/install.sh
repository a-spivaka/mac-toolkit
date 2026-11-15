#!/bin/bash
set -euo pipefail
ROOT="$(cd -- "$(dirname -- "$0")" && pwd)"
SHARE="$HOME/.local/share/image-toolkit"
SERVICES="$HOME/Library/Services"
[[ "$(uname -s)" == 'Darwin' ]] || { echo 'This package must be installed on macOS.' >&2; exit 1; }
[[ -x /usr/bin/sips ]] || { echo 'Missing /usr/bin/sips' >&2; exit 1; }
NAMES=(
  'Image - Convert to JPEG'
  'Image - Convert to PNG'
  'Image - Resize to 1600px'
  'Image - Web JPEG 1600px'
)
IDS=(
  'dev.chizh.image-toolkit.jpeg'
  'dev.chizh.image-toolkit.png'
  'dev.chizh.image-toolkit.resize1600'
  'dev.chizh.image-toolkit.web1600'
)
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
install -m 755 "$ROOT/image-toolkit.sh" "$SHARE/image-toolkit.sh"
for name in "${NAMES[@]}"; do
  target="$SERVICES/$name.workflow"
  if [[ -d "$target" ]]; then rm -rf -- "$target"; fi
  cp -R "$ROOT/$name.workflow" "$target"
done
if [[ -x /System/Library/CoreServices/pbs ]]; then /System/Library/CoreServices/pbs -update >/dev/null 2>&1 || true; fi
cat <<'MESSAGE'
Image Toolkit installed. In Finder, select one or more images and right-click:
  Quick Actions > Image - Convert to JPEG
  Quick Actions > Image - Convert to PNG
  Quick Actions > Image - Resize to 1600px
  Quick Actions > Image - Web JPEG 1600px

Output files are created alongside the originals. Originals are not overwritten.
If actions aren't visible, use Quick Actions > Customize (or System Settings > Login Items & Extensions).
You may delete the extracted installer folder after installation.
MESSAGE
