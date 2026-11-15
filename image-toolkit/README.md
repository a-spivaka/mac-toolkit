# Image Toolkit — Finder Quick Actions for macOS

A small, offline, no-dependencies (besides macOS' built-in `sips`) toolkit that Lior can install on her own Mac. Select one or more images in Finder and use **right click → Quick Actions**.

## What it installs

| Finder Quick Action | Result |
| --- | --- |
| **Image - Convert to JPEG** | New `_jpeg.jpg` copy at JPEG quality 85 |
| **Image - Convert to PNG** | New `_png.png` copy (supports transparency when source/decoder supports it) |
| **Image - Resize to 1600px** | New `_1600.<original extension>` copy; max width/height 1600px, aspect ratio maintained |
| **Image - Web JPEG 1600px** | New `_web.jpg` copy with max dimension 1600px, quality 80 |

* Images are processed locally, not uploaded.
* All original files are preserved. When output names collide, `(1)`, `(2)`, etc. are added.
* Output images are saved **next to their originals** (not in Downloads by default).
* Select several files at once for batch processing. Unsupported formats are skipped.
* JPEG does not support transparency. Use PNG for files where alpha/transparency matters.
* Converting/re-encoding is **not a privacy/metadata scrub**; do not assume EXIF/GPS will be removed.

**Two related actions are already built into recent macOS and deliberately not duplicated here:** Finder → Quick Actions → **Remove Background** produces a cutout PNG where supported; Finder → Quick Actions → **Convert Image** has an option to **turn off Preserve Metadata** when a clean sharing copy is needed. Their appearance can depend on the macOS version and enabled extensions. A clean copy should be checked before sharing sensitive images.

## Install on Lior's Mac

1. Download `image-toolkit.zip` on *her* Mac and unzip it in Downloads. You should see a directory named `image-toolkit`.
2. Open **Terminal** and run:

   ```bash
   cd ~/Downloads/image-toolkit && bash install.sh
   ```

3. In Finder, select an image → right click → **Quick Actions** → select an `Image - …` command.

If not visible: **Quick Actions → Customize…** and enable the actions (or System Settings → Login Items & Extensions).

The installer places the tool under `~/.local/share/image-toolkit` and each `.workflow` under `~/Library/Services`; the extracted installation directory can then be deleted. No Terminal window or background process is needed to use these on demand.

## Uninstall

From the extracted package:

```bash
bash uninstall.sh
```

If you've deleted the installer directory, download/unzip the ZIP again to run `uninstall.sh`.

## Troubleshooting

If a format is unsupported by the installed version of `sips`, the file will be skipped. Test from Terminal (substitute the path with a real image):

```bash
~/.local/share/image-toolkit/image-toolkit.sh web1600 "$HOME/Desktop/photo.heic"
```

The installer does not install Python, Homebrew, or third-party packages. macOS/Finder integration is not testable in this Linux build environment; the packaged workflows were checked for valid plist structure and the transformation flow was tested with a mocked `sips` command.
