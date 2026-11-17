# One-click Download Organizer and Python installer for family Macs

Download [Kids-Download-Organizer.zip](Kids-Download-Organizer.zip), extract it, and double-click **Install Download Organizer.command** from the macOS account to be configured.

This launcher detects Python 3.9+ and uses it when already available. If missing, it downloads **Python 3.15.2** (the official macOS installer, ~82 MB) from [python.org](https://www.python.org/downloads/release/python-3152/), verifies the published SHA-256 checksum and the macOS package signature, then opens the standard macOS Installer app. Complete the Installer (administrator credentials may be required), return to the original Terminal window and press Return. The Download Organizer will then install for the current user.

**Python is system-wide and only needs to be installed once.** Download Organizer is per-user: repeat the launcher once in each child's Mac account. Existing downloads and existing organizer configuration are preserved. Downloads are sorted in the background from then on.

The ZIP is small and does **not** bundle Python; Internet is required if Python is missing. No Git is required. Includes Hebrew instructions and an uninstall launcher. Uninstall removes only Download Organizer, not Python or downloads.

macOS may flag the downloaded unsigned .command script. Control-click -> Open and allow under Privacy & Security if necessary. Do not disable Gatekeeper globally.

Official installer: https://www.python.org/ftp/python/3.15.2/python-3.15.2-macos11.pkg

Published SHA-256: `2c6104475535b720b45774c68b0dfc9fcca2235353cf9ff81e05488f89845396`.
