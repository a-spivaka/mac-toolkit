# Download Organizer — one-click installer for family Macs

Download [Kids-Download-Organizer.zip](./Kids-Download-Organizer.zip) and extract it. While logged into the macOS account to configure, double-click **Install Download Organizer.command**. Repeat separately for each user.

The ZIP is self-contained (no Git or network needed to run it), but requires **Python 3.9+** on macOS. The installer uses the same `download-organizer/install.py` and assets as the toolkit and installs a per-user LaunchAgent. It preserves existing download files and any existing sorter configuration. On first install, it will only classify *new* downloads.

If macOS prevents opening the downloaded command, control-click the file and choose **Open**; follow the displayed security prompt. Do not disable Gatekeeper globally.

For uninstall, double-click **Uninstall Download Organizer.command**. Personal configs, logs, and downloads remain.

The ZIP contains the full script sources for inspection, plus Hebrew instructions.
