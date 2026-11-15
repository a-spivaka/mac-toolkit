# Git Actions — Finder Quick Actions for macOS

Read-only shortcuts in Finder for a Git repo, including files or subfolders within that repo. Works across any existing/new repository; install only once.

## Actions

| Finder Quick Action | Behavior |
| --- | --- |
| **Git - Show Status** | Opens a status report in TextEdit: branch, HEAD, upstream/ahead-behind, origin, changed/untracked files |
| **Git - Copy Working Diff** | Copies **staged + unstaged tracked changes** relative to `HEAD` (plus **names only** of untracked files) to the clipboard; selecting an individual file or a subdirectory limits this action to that path |
| **Git - Open PR** | On github.com origins: if `gh` CLI is installed and a matching PR exists, opens its direct URL; otherwise opens a list of PRs filtered to the current branch |
| **Git - Copy Context** | Copies a summary of the repo, branch, commit, upstream and Git status to clipboard |

No `git add`, `commit`, `push`, `fetch`, `pull`, `reset`, `rebase`, or merge commands are issued. Only one selected item at a time is supported. `Copy Working Diff` **does not include untracked file contents**, and intentionally refuses to copy a result larger than 512 KiB. Be mindful of secrets: raw diffs may contain sensitive content.

`Open PR` expects `origin` to resolve to **github.com**, using either SSH or HTTPS URLs. It doesn't fabricate a PR link; without working `gh` authentication it falls back to a filtered list. GitHub Enterprise and other providers aren't part of this version.

## Install once on your Mac

Requires Git and Python **3.8+** (already on many development Macs; Python may need to be installed separately). No Python packages are required.

1. Download `git-finder-actions.zip` and unzip it in Downloads. You should see a directory named `git-finder-actions`.
2. Open Terminal and run:

   ```bash
   cd ~/Downloads/git-finder-actions && bash install.sh
   ```

3. In Finder, right-click a repository folder or file inside it → **Quick Actions** → choose `Git - …`.

If actions are absent, use **Quick Actions → Customize…** (or System Settings → Login Items & Extensions). Terminal does not need to remain open.

The installed commands live in `~/.local/share/git-finder-actions/`, and Automator workflows in `~/Library/Services/`. The extracted directory can be deleted after installation.

## Direct CLI test (replace path)

```bash
~/.local/share/git-finder-actions/run.sh status "$HOME/path/to/repository"
~/.local/share/git-finder-actions/run.sh copy-context "$HOME/path/to/repository"
~/.local/share/git-finder-actions/run.sh copy-diff "$HOME/path/to/repository"
~/.local/share/git-finder-actions/run.sh open-pr "$HOME/path/to/repository"
```

Run `copy-diff` only after checking the diff doesn't contain secrets you intend to share; this tool copies locally to the clipboard but doesn't upload anything. The status report is stored in the local cache folder `~/Library/Caches/git-finder-actions/`.

## Uninstall

From the unzipped archive:

```bash
bash uninstall.sh
```

The installer only replaces workflows with matching bundle IDs; it leaves unrelated similarly named actions alone. The plist bundles and the Python code were validated in a Linux test environment, but Finder behavior needs to be verified on the destination Mac.
