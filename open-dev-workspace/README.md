# Open Development Workspace — Finder Quick Action

A right-click action for macOS Finder that opens a **Git working tree** in Visual Studio Code, Terminal, and (if the `origin` remote belongs to `github.com`) your browser. The script reads Git metadata but makes **no edits, commits, fetches, pulls, or pushes**.

## Installation

1. Extract `open-dev-workspace.zip` in Downloads.
2. In Terminal run:

   ```bash
   cd ~/Downloads/open-dev-workspace && bash install.sh
   ```

3. In Finder, right-click a folder inside a Git repository and choose **Quick Actions → Open Development Workspace** (or **Services**).

The script is copied to `~/.local/share/open-dev-workspace/open-workspace.sh` and the Finder action to `~/Library/Services/Open Development Workspace.workflow`. After installation, the downloaded ZIP and extracted folder may be removed.

If Finder does not show the action, check **Finder → Quick Actions → Customize**, or **System Settings → Keyboard → Keyboard Shortcuts → Services**. Some macOS versions need a Finder relaunch or logout/login before a new Quick Action appears.

## What it does

- Resolves the Git root even if you selected a subfolder.
- Opens the repository root in **Visual Studio Code** (`com.microsoft.VSCode`).
- Opens a **Terminal** window whose working directory is the repository root.
- Opens the `origin` GitHub page if the URL is a recognized `github.com` SSH/HTTPS remote.
- Displays a notification with branch, count of changed/untracked files, and commits ahead of the configured upstream. No upstream → says so (does not falsely imply zero commits).
- Does not attempt to open URLs from arbitrary remotes or remote URLs with embedded credentials.

VS Code and Git should be installed; GitHub is optional. The GitHub page opens in your default browser. Launching Terminal may prompt for Automation permissions.

## Test, diagnostics

You can test from Terminal without opening VS Code, Terminal, or a browser:

```bash
~/.local/share/open-dev-workspace/open-workspace.sh --dry-run /path/to/repository
```

Expected output includes Repository, Branch, Changed files, Commits, and GitHub URL. This also works on a nested folder inside the repo.

## Remove

Before deleting the extracted directory, you can use `bash uninstall.sh` from it. If you've deleted it, re-extract the ZIP and run the same command. The uninstall script removes only this Quick Action and its installed script (and verifies the workflow identifier before removing it).

## Notes

- Select exactly **one folder**. It will refuse files, multiple selections, or folders outside Git repositories.
- macOS Finder Services sometimes don't become visible immediately after installation.
- On Apple Silicon and Intel Macs, `open -b com.microsoft.VSCode` avoids depending on the `code` CLI being installed.
- The script does not configure VS Code or Git and does not depend on Chizh itself.
- This package is assembled and statically tested on Linux; Finder integration cannot be executed or validated until installed on macOS.
