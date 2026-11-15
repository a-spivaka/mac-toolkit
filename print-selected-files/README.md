# Print Selected Files — Finder Quick Actions (macOS)

Two actions for any selection of PDFs/images in Finder:

- **Print Selected Files**: creates one merged PDF and **submits it immediately to the default printer** (`lp`). No preview or confirmation dialog. This is a change from v1, which only opened Preview.
- **Preview Selected Files**: creates the same merged PDF and opens it in Preview, without printing. Use **⌘P** there if you want to pick a printer, adjust copies/duplex, etc.

**Caution:** the first action sends a real print job, so make sure the default printer is the one you want before invoking it.

## Install (or update) once

1. Unzip the package into `~/Downloads/print-selected-files`.
2. In Terminal:

   ```bash
   cd ~/Downloads/print-selected-files && bash install.sh
   ```

3. In Finder select PDF/images -> right-click -> Quick Actions -> **Print Selected Files** or **Preview Selected Files**.
4. If the action does not appear: System Settings -> Keyboard -> Keyboard Shortcuts -> Services -> Files and Folders, enable it. Finder may need to be relaunched.

The install script replaces the previously installed Print action and adds the new Preview action. No need to uninstall the old one first.

## Printer setup

`Print Selected Files` uses CUPS command `lp` and the default printer selected by CUPS. Verify printer settings in **System Settings -> Printers & Scanners**. In Terminal you can check:

```bash
lpstat -p -d
```

You can choose a specific CUPS default by running `lpoptions -d PRINTER_NAME`. This modifies the user-level CUPS preference. A print job successfully queued is not a guarantee the printer has finished printing: check the printer queue if nothing comes out.

**No confirmation prompt:** the printing action uses the default printer's default settings for paper, color, duplex, copies, etc. Use **Preview Selected Files** if you want to change settings per job.

## Supported inputs and sorting

- PDF: preserves every page, in original order.
- PNG, JPEG, HEIC/HEIF, TIFF, BMP, GIF (first GIF frame): one PDF page per image.
- Mixed selections are sorted by filename with natural numeric sort (`2` before `10`), not click order. Prefix filenames `01-`, `02-` to control the order.
- Unsupported types/password-protected PDFs cause an error; originals are never modified.

## Local data, errors and cleanup

- Uses built-in PDFKit via `osascript`; printing via built-in CUPS `lp`. No external dependencies.
- Temporary merged PDFs are stored in `~/Library/Caches/Print Selected Files/job-*`; those older than 7 days are cleaned on a later run.
- Merge/print errors: `~/Library/Caches/Print Selected Files/last-error.log`.
- The print job receipt is in `job-*/print-receipt.txt`.
- The script does not upload files or modify the selected files.

## Uninstall

```bash
cd ~/Downloads/print-selected-files && bash uninstall.sh
```

To uninstall without the extracted source folder, remove these two workflows and the `~/Library/Application Support/Print Selected Files` folder.

## CLI check

```bash
"$HOME/Library/Application Support/Print Selected Files/print-selected-files.sh" "$HOME/Downloads/1.pdf" "$HOME/Downloads/2.jpg"
```

Add `--preview` as first argument to open instead of printing.

**Compatibility note:** this bundle was verified with syntax and workflow-structure checks in a Linux environment. PDFKit/Printer integration should be tested on macOS with a small document.
