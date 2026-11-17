#!/bin/bash
# Download Organizer installer for macOS. Runs only for the current signed-in user.
set -u
cd "$(dirname "$0")" || exit 1

echo "===================================================="
echo "  Download Organizer - Setup for this Mac user"
echo "===================================================="
echo
echo "Installs only the download sorter; no other toolkit utilities."
echo "Existing downloads will be left untouched."
echo

if ! command -v python3 >/dev/null 2>&1; then
  echo "Python 3 is required but was not found on this Mac."
  echo "Install Python 3 from: https://www.python.org/downloads/macos/"
  open "https://www.python.org/downloads/macos/" >/dev/null 2>&1 || true
  echo
  read -r -p "Press Return to close..." _
  exit 1
fi
if ! python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3, 9) else 1)' >/dev/null 2>&1; then
  echo "Python 3.9 or newer is required."
  echo "Update Python: https://www.python.org/downloads/macos/"
  echo
  read -r -p "Press Return to close..." _
  exit 1
fi

if bash "./download-organizer/install.sh"; then
  echo
  echo "SUCCESS: Download Organizer is installed for this user."
  echo "New downloads will be sorted into Docs, Images, Media,"
  echo "Archives, Installers and other folders automatically."
  echo "Existing downloads remain as they are."
  echo "Log out and repeat the same installation for each other child."
else
  echo
  echo "Installation failed. Please copy the error above."
fi
echo
read -r -p "Press Return to close this window..." _
