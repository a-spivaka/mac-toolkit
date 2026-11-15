#!/bin/bash
# Finder Quick Actions receive one pathname per argument.
set -euo pipefail
export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
APP="$HOME/.local/share/prepare-debug-bundle/bundle.py"
LOG="$HOME/Library/Logs/prepare-debug-bundle.log"
mkdir -p "$(dirname "$LOG")"

notify_failure() {
  /usr/bin/osascript -e 'display notification "Open ~/Library/Logs/prepare-debug-bundle.log for details" with title "Prepare Debug Bundle failed"' >/dev/null 2>&1 || true
}

if ! command -v python3 >/dev/null 2>&1; then
  echo "Python 3 not found; install Python 3 before using this Quick Action." >> "$LOG"
  notify_failure
  exit 1
fi

if ! "$(command -v python3)" "$APP" --reveal "$@" >> "$LOG" 2>&1; then
  notify_failure
  exit 1
fi
