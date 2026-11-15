# Download Organizer — Media rule update

Adds video and audio file extensions to the existing Download Organizer configuration and creates `~/Downloads/Media`. The original JSON rules, custom destinations, and script installation are preserved.

Run after extracting the zip into Downloads:

```bash
cd ~/Downloads/download-organizer-media-update
bash update.sh
```

No restart of `launchd` is required. New downloads are routed on the next scheduled run (subject to the existing stability check). Files present when Download Organizer was first initialized remain excluded. Media downloaded afterward but not previously matched may move automatically when the new rule is loaded.

Extensions: `.mp4`, `.mov`, `.m4v`, `.mkv`, `.avi`, `.webm`, `.wmv`, `.mpg`, `.mpeg`, `.3gp`, `.m2ts`, `.mp3`, `.m4a`, `.aac`, `.wav`, `.flac`, `.ogg`, `.opus`, `.aiff`. `.ts` is deliberately excluded because it also denotes TypeScript source files.

The update backs up the installed config before any edit with a `.backup-<timestamp>` suffix. If a `Media` rule already exists, the updater adds missing extensions rather than creating a duplicate. You can edit the destination later in `~/.config/download-organizer/config.json`.

If an **already-downloaded video** does not move after the update, drag it manually from Downloads to Media. Files excluded at the original installation will stay excluded.
