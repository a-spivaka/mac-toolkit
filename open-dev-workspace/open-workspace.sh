#!/bin/bash
# Finder Quick Action: open a Git worktree in VS Code, Terminal, and GitHub.
# Only reads Git state; never changes repository files or Git configuration.
set -euo pipefail

usage() {
  printf 'Usage: %s [--dry-run] <repository-folder>\n' "$0" >&2
  exit 2
}

fail() {
  printf 'Open Development Workspace: %s\n' "$1" >&2
  if [[ "$DRY_RUN" == "0" ]] && command -v osascript >/dev/null 2>&1; then
    /usr/bin/osascript - "$1" <<'APPLESCRIPT' >/dev/null 2>&1 || true
on run args
  display alert "Open Development Workspace" message (item 1 of args) as warning
end run
APPLESCRIPT
  fi
  exit 1
}

DRY_RUN=0
if [[ "${1:-}" == "--dry-run" ]]; then
  DRY_RUN=1
  shift
fi
[[ "$#" -eq 1 ]] || usage
selected="$1"
[[ -d "$selected" ]] || fail "Choose a folder in Finder (not a file)."
command -v git >/dev/null 2>&1 || fail "Git is not installed or not available in PATH."

repo="$(git -C "$selected" rev-parse --show-toplevel 2>/dev/null)" || fail "The selected folder is not inside a Git repository."
[[ -d "$repo" ]] || fail "Git returned a non-existent worktree directory."

branch="$(git -C "$repo" symbolic-ref --quiet --short HEAD 2>/dev/null || true)"
if [[ -z "$branch" ]]; then
  branch="detached @ $(git -C "$repo" rev-parse --short HEAD 2>/dev/null || printf 'unknown')"
fi

status="$(git -C "$repo" status --porcelain=v1 --untracked-files=normal 2>/dev/null || true)"
changes=0
if [[ -n "$status" ]]; then
  while IFS= read -r line; do
    [[ -n "$line" ]] && changes=$((changes + 1))
  done <<< "$status"
fi

if git -C "$repo" rev-parse --verify --quiet '@{upstream}' >/dev/null 2>&1; then
  ahead="$(git -C "$repo" rev-list --count '@{upstream}..HEAD' 2>/dev/null || printf '?')"
  ahead_message="${ahead} unpushed commit(s)"
else
  ahead_message="no tracking upstream"
fi

# Only open a verified github.com origin; never pass credentials or arbitrary schemes to a browser.
github_url=""
remote="$(git -C "$repo" remote get-url origin 2>/dev/null || true)"
case "$remote" in
  git@github.com:*) github_path="${remote#git@github.com:}" ;;
  ssh://git@github.com/*) github_path="${remote#ssh://git@github.com/}" ;;
  https://github.com/*) github_path="${remote#https://github.com/}" ;;
  *) github_path="" ;;
esac
if [[ -n "$github_path" ]]; then
  github_path="${github_path%.git}"
  github_path="${github_path%/}"
  # Exactly two URL-safe path components, no dot/dot-dot path segments.
  if [[ "$github_path" =~ ^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$ ]] &&
     [[ "$github_path" != ../* ]] && [[ "$github_path" != */.. ]] &&
     [[ "$github_path" != ./* ]] && [[ "$github_path" != */. ]]; then
    github_url="https://github.com/$github_path"
  fi
fi

printf 'Repository: %s\nBranch: %s\nChanged files: %s\nCommits: %s\nGitHub: %s\n' \
  "$repo" "$branch" "$changes" "$ahead_message" "${github_url:-not configured (or not github.com)}"

if [[ "$DRY_RUN" == "1" ]]; then
  printf 'Dry run: did not open any apps.\n'
  exit 0
fi

# VS Code: use the standard bundle ID with application-name fallback.
if ! /usr/bin/open -b com.microsoft.VSCode "$repo" >/dev/null 2>&1; then
  if ! /usr/bin/open -a "Visual Studio Code" "$repo" >/dev/null 2>&1; then
    printf 'Warning: VS Code could not be opened. Is it installed?\n' >&2
  fi
fi

# Open the repository URL independently of Terminal automation permissions.
# If macOS blocks AppleScript control of Terminal, GitHub should still open.
if [[ -n "$github_url" ]]; then
  if ! /usr/bin/open "$github_url" >/dev/null 2>&1; then
    printf 'Warning: Could not open GitHub URL: %s\n' "$github_url" >&2
  fi
else
  printf 'Note: GitHub skipped because origin is missing or not a recognized github.com remote.\n' >&2
fi

# Terminal's `quoted form` ensures paths containing quotes, whitespace, etc. are shell-safe.
if ! /usr/bin/osascript - "$repo" <<'APPLESCRIPT' >/dev/null
on run args
  set repoPath to item 1 of args
  tell application "Terminal"
    activate
    do script "cd " & quoted form of repoPath
  end tell
end run
APPLESCRIPT
then
  printf 'Warning: Could not open Terminal in this repo; check macOS Automation permissions.\n' >&2
fi

# Notification is informational and optional (depends on macOS notification permissions).
/usr/bin/osascript - "$(basename "$repo")" "$branch" "$changes" "$ahead_message" <<'APPLESCRIPT' >/dev/null 2>&1 || true
on run args
  set repoName to item 1 of args
  set branchName to item 2 of args
  set changedCount to item 3 of args
  set aheadInfo to item 4 of args
  display notification ("Branch: " & branchName & " · Changed: " & changedCount & " · " & aheadInfo) with title ("Workspace: " & repoName)
end run
APPLESCRIPT
