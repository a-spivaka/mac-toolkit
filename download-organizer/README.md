# Download Organizer for macOS

Organizes **completed** new downloads from `~/Downloads`, based on filename and extension. Works with Chrome PDFs saved using **Save As**, as long as you save them to Downloads.

## Installation (no dependencies except Python 3)

Extract the zip, open Terminal in the extracted folder, and run:

```bash
bash install.sh
```

The installer creates and loads `~/Library/LaunchAgents/local.download-organizer.plist` using Apple's `launchd` service (no administrator privileges). The service runs when the Downloads folder changes, with a backup check every 20 seconds. To avoid moving an in-progress download, it waits until a file's size and metadata have remained unchanged for at least 12 seconds, *across separate scans*. Most downloads move within approximately 20–40 seconds after completion; some take longer.

**Important:** The installer leaves **all existing files** in Downloads alone. It does not delete anything, and if a destination has the same filename, the new file receives a numeric suffix such as `(1)`.

## Your rules

Edit:

```bash
open -e "$HOME/.config/download-organizer/config.json"
```

Rules are checked **top to bottom; first match wins**. `extensions` matches the end of the filename, case-insensitively. `filename_globs` is optional and supports `*` and `?`. **When a rule has both, both must match.**

Example: `chizh-...log` routes to `~/Downloads/Chizh`, all PDFs/DOC/DOCX to `~/Downloads/Docs`, and images to `~/Downloads/Images`. Each destination can be changed to any directory that your account can write to. The target folder is created automatically on the first matching move.

There is no need to reload the LaunchAgent after editing the JSON: the next invocation reads the config again.

## Test safely

Preview all current files, including downloads from before the installation, without touching them:

```bash
python3 "$HOME/.local/share/download-organizer/download_organizer.py" --dry-run --all --now
```

Check recent moves and errors:

```bash
tail -n 40 "$HOME/Library/Logs/download-organizer.out.log"
tail -n 40 "$HOME/Library/Logs/download-organizer.err.log"
```

To process old files as well (opt-in):

```bash
python3 "$HOME/.local/share/download-organizer/download_organizer.py" --all
```

That last command marks old files as candidates. They will only move after a second scan verifies they have remained unchanged for the configured settle period. It is intended for use while the regular agent is running; note that the agent normally skips old files so you may need to run `--all` a second time after 12 seconds to move the old files.

## Practical caveats

- For Chrome's PDF viewer, the **Save As dialog may still appear**; choose `Downloads`. This tool organizes the saved file afterward.
- Downloads saved *directly to a different folder* will not be picked up. Only files directly inside `~/Downloads` are scanned; subdirectories are not scanned.
- Temporary files (`.crdownload`, `.download`, `.part`, `.partial`, `.tmp`) and hidden files are ignored.
- The stability wait reduces risk but is not an absolute guarantee against unusually stalled downloads: do not use this as a transfer-integrity verifier.
- macOS may require permission to access Downloads for the Python interpreter, Terminal, or background process. Grant access if macOS prompts you.
- Avoid running a different Chrome sorting extension for the same download categories; otherwise they may conflict. Disable its rules once you switch.

## Uninstall

From the extracted bundle:

```bash
bash uninstall.sh
```

This disables the background job and removes its installed executable. It does **not** remove the configuration, saved state, logs or any downloads.
