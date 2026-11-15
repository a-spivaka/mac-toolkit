# Prepare Debug Bundle — Finder Quick Action

Create a self-contained ZIP of **selected regular files** directly from Finder. Particularly useful for bundling logs, JSON outputs, screenshots, and small reproductions when investigating problems.

## Install (once)

1. Unzip `prepare-debug-bundle.zip` into Downloads.
2. Open Terminal and run:

   ```bash
   cd ~/Downloads/prepare-debug-bundle && bash install.sh
   ```

3. In Finder, **select multiple files** → right-click → **Quick Actions → Prepare Debug Bundle** (or **Services** on some macOS versions).
4. The resulting ZIP appears in `~/Downloads/Debug-Bundles/`. Finder should automatically reveal it.

The installer copies the Python script and workflow to permanent locations. You can delete the extracted installation folder and its ZIP afterward.

**Prerequisite:** Python 3 on your Mac (no third-party Python packages). If Python is installed through Homebrew, the Finder action searches `/opt/homebrew/bin`, `/usr/local/bin`, and the system paths.

## ZIP contents

```text
debug-bundle-20261101-130000-abcd1234.zip
├── README.txt
├── manifest.json
└── files/
    ├── 001/
    │   └── app.log
    ├── 002/
    │   └── response.json
    └── 003/
        └── screenshot.png
```

`manifest.json` contains each original **filename**, archive path, file size, UTC modification time, and SHA-256 digest, plus archive creation time. Absolute source paths are not included in the manifest. The numeric directory prevents collisions between identically named input files.

## Safety and limits

- **Read-only input:** source files are never renamed, moved, deleted, or modified.
- Only explicitly selected **regular files** are accepted; directories and symbolic links are refused. This avoids accidentally zipping an entire repository, `.git`, or unrelated folders.
- Blocks obviously sensitive filenames (`.env*`, private keys, credentials, etc.) by default. Customize these rules in `config.json`.
- Default size limits: **100 files**, **100 MiB per file**, **300 MiB total uncompressed**. If any file fails validation, nothing is published.
- ZIP is assembled under a hidden temporary name and published only when complete, without overwriting an existing ZIP.
- Detects common cases where a file is replaced or modified during compression and aborts the whole bundle.
- **IMPORTANT: file contents are NOT scanned or redacted for secrets.** Logs and JSON may contain tokens, passwords, personal information, or internal data. **Review the archive before sharing it.** A filename rule is not a data-leak prevention system.
- Entirely local. No uploads or network calls.

## Configuration

After installation, edit:

```bash
open -e ~/.config/prepare-debug-bundle/config.json
```

Example:

```json
{
  "output_directory": "~/Downloads/Debug-Bundles",
  "max_files": 100,
  "max_file_mb": 100,
  "max_total_mb": 300,
  "blocked_extensions": [".pem", ".key", ".p12", ".pfx", ".p8", ".kdbx"],
  "blocked_filename_regex": ["^\\.env($|\\.)", "(^|[._-])id_(rsa|ed25519|ecdsa)($|[._-])", "(^|[._-])(private[-_ ]?key|credentials?|secrets?)($|[._-])"]
}
```

Changes take effect on the next invocation, without a reinstall.

## Test from Terminal

Use your own existing files; in a terminal you can run:

```bash
python3 ~/.local/share/prepare-debug-bundle/bundle.py --dry-run \
  ~/Downloads/example.log ~/Downloads/example.json
```

To create the bundle, omit `--dry-run`. You can also use `--reveal` to show the output in Finder.

If Finder's action appears to do nothing, examine:

```bash
tail -n 40 ~/Library/Logs/prepare-debug-bundle.log
```

If the action does not appear, look in **System Settings → Keyboard → Keyboard Shortcuts → Services → Files and Folders** or the Finder **Quick Actions → Customize** menu. Try a Finder relaunch or log out and back in if necessary. macOS may prompt for access to protected folders.

## Uninstall

Run `bash uninstall.sh` from the extracted package. It removes the Quick Action and installed scripts **but preserves** your settings and existing ZIPs. You can re-download the ZIP if you've deleted the original folder.

## Files installed

- `~/.local/share/prepare-debug-bundle/bundle.py`
- `~/.local/share/prepare-debug-bundle/run.sh`
- `~/.config/prepare-debug-bundle/config.json`
- `~/Library/Services/Prepare Debug Bundle.workflow`

## Testing note

The Python CLI and ZIP output are tested in this development environment. Finder integration and macOS permissions require a test on your own Mac.
