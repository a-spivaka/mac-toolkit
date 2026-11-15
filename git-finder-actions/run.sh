#!/bin/bash
set -euo pipefail
export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:$PATH"
PYTHON_BIN="${PYTHON3_PATH:-}"
if [[ -z "$PYTHON_BIN" ]]; then
  for candidate in /opt/homebrew/bin/python3 /usr/local/bin/python3 /usr/bin/python3; do
    if [[ -x "$candidate" ]] && "$candidate" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)' >/dev/null 2>&1; then
      PYTHON_BIN="$candidate"
      break
    fi
  done
fi
[[ -n "$PYTHON_BIN" ]] || { echo 'Python 3.8+ is required.' >&2; /usr/bin/osascript -e 'display alert "Git Actions" message "Python 3.8+ is required. Install Python 3 and run the action again."' >/dev/null 2>&1 || true; exit 1; }
exec "$PYTHON_BIN" "$HOME/.local/share/git-finder-actions/git_actions.py" "$@"
