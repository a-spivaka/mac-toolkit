#!/bin/bash
# Kids Download Organizer: install Python 3 if needed, then the per-user organizer.
set -u
cd "$(dirname "$0")" || exit 1

pause() {
  echo
  read -r -p "Press Return to close this window..." _ || true
}
fail() {
  echo
  echo "ERROR: $1"
  pause
  exit 1
}
find_python() {
  local p
  for p in \
    "/Library/Frameworks/Python.framework/Versions/Current/bin/python3" \
    "/Library/Frameworks/Python.framework/Versions/3.15/bin/python3" \
    "/Library/Frameworks/Python.framework/Versions/3.14/bin/python3" \
    "/Library/Frameworks/Python.framework/Versions/3.13/bin/python3" \
    "/Library/Frameworks/Python.framework/Versions/3.12/bin/python3" \
    "/Library/Frameworks/Python.framework/Versions/3.11/bin/python3" \
    "/Library/Frameworks/Python.framework/Versions/3.10/bin/python3" \
    "/Library/Frameworks/Python.framework/Versions/3.9/bin/python3" \
    "/opt/homebrew/bin/python3" \
    "/usr/local/bin/python3" \
    "$(command -v python3 2>/dev/null || true)"; do
    [ -n "$p" ] && [ -x "$p" ] || continue
    if "$p" -c 'import sys; sys.exit(0 if sys.version_info >= (3,9) else 1)' >/dev/null 2>&1; then
      echo "$p"
      return 0
    fi
  done
  return 1
}

[ "$(uname -s)" = "Darwin" ] || fail "This installer requires macOS."
echo "===================================================="
echo " Kids Download Organizer - Setup"
echo "===================================================="
echo
echo "Installing Download Organizer for the CURRENT Mac user."
echo "Existing Downloads files will not be moved or deleted."
echo

PYTHON="$(find_python || true)"
if [ -n "$PYTHON" ]; then
  echo "Found Python: $("$PYTHON" --version 2>&1)"
else
  PYTHON_VERSION="3.15.2"
  PYTHON_URL="https://www.python.org/ftp/python/$PYTHON_VERSION/python-$PYTHON_VERSION-macos11.pkg"
  EXPECTED_SHA256="2c6104475535b720b45774c68b0dfc9fcca2235353cf9ff81e05488f89845396"
  echo "Python 3.9+ not found. Downloading official Python $PYTHON_VERSION (~82 MB)."
  echo
  TMP_PYTHON_DIR="$(mktemp -d "/tmp/kids-python-install.XXXXXX")" || fail "Cannot create temporary directory."
  trap 'rm -rf "$TMP_PYTHON_DIR"' EXIT
  PYTHON_PKG="$TMP_PYTHON_DIR/python-$PYTHON_VERSION-macos11.pkg"
  if ! /usr/bin/curl --fail --location --retry 3 --connect-timeout 20 --output "$PYTHON_PKG" "$PYTHON_URL"; then
    fail "Python download failed. Check your Internet connection."
  fi
  ACTUAL_SHA256="$(/usr/bin/shasum -a 256 "$PYTHON_PKG" | /usr/bin/awk '{print $1}')"
  if [ "$ACTUAL_SHA256" != "$EXPECTED_SHA256" ]; then
    fail "Python package checksum did not match. Nothing was installed."
  fi
  if ! /usr/sbin/pkgutil --check-signature "$PYTHON_PKG" >/dev/null 2>&1; then
    fail "Python package signature check failed. Nothing was installed."
  fi
  echo "Official Python package verified (SHA-256 + package signature)."
  echo
  echo "Opening the macOS Installer. Complete all Installer steps."
  echo "You may be asked for a Mac administrator username and password."
  echo "When installation succeeds, return to THIS Terminal window."
  if ! /usr/bin/open "$PYTHON_PKG"; then
    fail "Could not open the Python installer."
  fi
  while :; do
    echo
    read -r -p "After installing Python, press Return here (or q to quit): " REPLY || fail "No input."
    if [ "$REPLY" = "q" ] || [ "$REPLY" = "Q" ]; then
      echo "Cancelled: Download Organizer was not installed."
      exit 1
    fi
    PYTHON="$(find_python || true)"
    [ -n "$PYTHON" ] && break
    echo "Python is not available yet; finish installing it and press Return again."
  done
  echo "Python installed: $("$PYTHON" --version 2>&1)"
fi
echo
echo "Installing Download Organizer for $(id -un)..."
if "$PYTHON" "./download-organizer/install.py"; then
  echo
  echo "SUCCESS: Python and Download Organizer are ready."
  echo "New files in Downloads will be sorted (Docs, Images, Media, etc.)."
  echo "Existing downloaded files remain untouched."
  echo "Repeat this setup once for each other child's Mac account."
  pause
  exit 0
else
  fail "Download Organizer installation failed. See the error above."
fi
