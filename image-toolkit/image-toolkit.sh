#!/bin/bash
# Finder Image Toolkit: one-click, non-destructive batch transformations using macOS sips.
set -euo pipefail

SIPS_BIN="${SIPS_BIN:-/usr/bin/sips}"
NOTIFY_BIN="${NOTIFY_BIN:-/usr/bin/osascript}"

usage() {
  cat >&2 <<'USAGE'
Usage: image-toolkit.sh {jpeg|png|resize1600|web1600} IMAGE [IMAGE ...]
  jpeg       Convert to high-quality JPG (85% quality).
  png        Convert to PNG.
  resize1600 Copy at no more than 1600 px on either edge; preserve original format.
  web1600    Convert to JPG, max 1600 px, 80% quality.
Output is created beside each original, with a suffix; originals are untouched.
USAGE
  exit 2
}

[[ $# -ge 2 ]] || usage
MODE="$1"; shift
case "$MODE" in jpeg|png|resize1600|web1600) ;; *) usage ;; esac
[[ -x "$SIPS_BIN" ]] || { echo "Missing sips: $SIPS_BIN" >&2; exit 1; }

# Create a unique destination without replacing any existing file.
unique_dest() {
  local dir="$1" base="$2" ext="$3" n=0 candidate
  candidate="$dir/$base.$ext"
  while [[ -e "$candidate" || -L "$candidate" ]]; do
    n=$((n+1))
    candidate="$dir/$base ($n).$ext"
  done
  printf '%s\n' "$candidate"
}

success=0
failed=0
for src in "$@"; do
  if [[ ! -f "$src" || -L "$src" ]]; then
    echo "SKIP (not a regular image file): $src" >&2
    failed=$((failed+1))
    continue
  fi
  # Ignore image-like names that sips cannot decode.
  if ! "$SIPS_BIN" -g format "$src" >/dev/null 2>&1; then
    echo "SKIP (unsupported image): $src" >&2
    failed=$((failed+1))
    continue
  fi
  dir="$(dirname "$src")"
  filename="$(basename "$src")"
  if [[ "$filename" == *.* && "$filename" != .* ]]; then
    stem="${filename%.*}"
    source_ext="${filename##*.}"
  else
    stem="$filename"
    source_ext=""
  fi
  case "$MODE" in
    jpeg) outbase="${stem}_jpeg"; extension="jpg" ;;
    png) outbase="${stem}_png"; extension="png" ;;
    web1600) outbase="${stem}_web"; extension="jpg" ;;
    resize1600)
      outbase="${stem}_1600"
      # Keep original format. sips might reject unsupported writable formats.
      extension="${source_ext:-png}"
      ;;
  esac
  dest="$(unique_dest "$dir" "$outbase" "$extension")"
  if case "$MODE" in
      jpeg) "$SIPS_BIN" -s format jpeg -s formatOptions 85 "$src" --out "$dest" >/dev/null ;;
      png) "$SIPS_BIN" -s format png "$src" --out "$dest" >/dev/null ;;
      resize1600) "$SIPS_BIN" -Z 1600 "$src" --out "$dest" >/dev/null ;;
      web1600) "$SIPS_BIN" -s format jpeg -s formatOptions 80 -Z 1600 "$src" --out "$dest" >/dev/null ;;
    esac; then
    success=$((success+1))
    echo "CREATED $dest"
  else
    # Remove incomplete output produced by a failed sips invocation.
    rm -f -- "$dest"
    echo "FAILED $src" >&2
    failed=$((failed+1))
  fi
done

if [[ "$(uname -s)" == "Darwin" && -x "$NOTIFY_BIN" ]]; then
  # Only constant text is passed to AppleScript, not file paths.
  "$NOTIFY_BIN" -e "display notification \"Created $success image(s); failed/skipped $failed.\" with title \"Image Toolkit\"" >/dev/null 2>&1 || true
fi
[[ $failed -eq 0 ]]
