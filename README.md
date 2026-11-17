# Mac Toolkit

A collection of six independent macOS automation utilities. Finder actions and a background download organizer, built with Python, shell scripts, JavaScript for Automation, and native macOS components.

> **Privacy:** This repository is public. Checked-in configuration files are example defaults only; personal installed settings are stored in `~/.config/` and are not committed. Review generated logs or bundles before sharing.

These are the six standalone macOS tools from our conversation. Each folder contains its own installer and documentation. Nothing runs automatically from unpacking this archive.

| Tool | macOS behavior | Setup |
| --- | --- | --- |
| `download-organizer` | Classifies completed downloads by name/extension. Includes Media, Docs, Images, Archives, Installers, Chizh logs. Uses launchd. | `cd download-organizer && bash install.sh` |
| `open-dev-workspace` | Finder Quick Action opens repo in VS Code, Terminal, and GitHub where configured. Contains the GitHub-opening fix. | `cd open-dev-workspace && bash install.sh` |
| `prepare-debug-bundle` | Finder Quick Action creates a ZIP of selected files with manifest and SHA-256; no secret-content scan. | `cd prepare-debug-bundle && bash install.sh` |
| `image-toolkit` | Finder Quick Actions convert JPEG/PNG, resize to 1600px, or create compressed web JPEGs. Intended for Lior’s Mac. | `cd image-toolkit && bash install.sh` |
| `git-finder-actions` | Finder Quick Actions for Show Status, Copy Working Diff, Open PR, Copy Context. Read-only Git. | `cd git-finder-actions && bash install.sh` |
| `print-selected-files` | Finder Quick Actions merge selected PDFs/images, then either print directly to default printer or preview. **Print sends a real job without confirmation.** | `cd print-selected-files && bash install.sh` |

## Updating existing installations

- **Download Organizer:** The standard installer preserves `~/.config/download-organizer/config.json` and will not overwrite your personalized rules. If you have not already added Media, run `bash updates/download-organizer-media-update/update.sh` from the collection directory. This updates the existing config and makes a backup.
- **Open Development Workspace:** The installer refuses to overwrite an existing Finder action. If already installed, run `bash open-dev-workspace/update.sh` to apply the GitHub fix to the installed script.
- **Print Selected Files:** `bash print-selected-files/install.sh` updates the existing workflow and adds Preview Selected Files. Be aware that Print Selected Files immediately submits a printer job.
- **Other tools:** Reinstall only as needed, following each tool’s README; do not assume an installer safely updates an existing installation.

## Configuration and storage

- Download Organizer rules: `~/.config/download-organizer/config.json` (initially watches `~/Downloads`; new destinations can be customized).
- Debug bundle settings: `~/.config/prepare-debug-bundle/config.json`; default bundle output is `~/Downloads/Debug-Bundles`.
- Automator Quick Actions live under `~/Library/Services/` and can be invoked from Finder’s right-click menu.
- Most tools only run when invoked; only Download Organizer installs a background LaunchAgent.

## Important limitations

- Files saved from the Chrome PDF viewer may still show Save As; save into `~/Downloads` for Download Organizer to move them afterward.
- Untracked file contents are not included in Git Copy Working Diff. Inspect copied diffs before sharing them.
- Image Toolkit conversions are not guaranteed to remove metadata/GPS information.
- The printing workflow has been statically tested, but actual printing, Finder actions, and AppleScript/PDFKit must be checked on the destination Mac.
- These tools operate locally and are not installed by this archive until you explicitly run an installer.

## One-click Download Organizer for family Macs

For a separate macOS account (such as a child's account), download **[Kids-Download-Organizer.zip](dist/Kids-Download-Organizer.zip)**, unzip it, then double-click **Install Download Organizer.command** inside. It installs only the per-user download sorter. Requires Python 3.9+; existing downloads are left untouched. Hebrew instructions and an uninstaller are included in the ZIP. See [installer details](dist/README.md).
