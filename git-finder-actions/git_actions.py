#!/usr/bin/env python3
"""Read-only Finder Git Quick Actions. Python 3 stdlib, git, optional GitHub CLI."""
import argparse
import hashlib
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
from urllib.parse import quote, urlparse

MAX_DIFF_BYTES = 512 * 1024
MAX_GIT_OUTPUT = 2 * 1024 * 1024


class ActionError(Exception):
    pass


def git(repo: Path, *arguments: str, check: bool = True) -> str:
    command = ['git', '--no-optional-locks', '-C', str(repo), *arguments]
    try:
        proc = subprocess.run(command, text=True, encoding='utf-8', errors='replace',
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                              timeout=20, env={**os.environ, 'GIT_TERMINAL_PROMPT': '0'})
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise ActionError(f'Could not run git: {exc}') from exc
    if proc.returncode and check:
        raise ActionError(proc.stderr.strip()[:300] or 'Git command failed')
    if len(proc.stdout.encode('utf-8')) > MAX_GIT_OUTPUT:
        raise ActionError('Git output exceeds safety limit')
    return proc.stdout.strip('\n') if not proc.returncode else ''


def repo_for(selected: str):
    path = Path(selected).expanduser().resolve()
    if not path.exists():
        raise ActionError(f'Path does not exist: {selected}')
    root = path if path.is_dir() else path.parent
    top = git(root, 'rev-parse', '--show-toplevel')
    if not top:
        raise ActionError('Selection is not inside a Git repository')
    repo = Path(top).resolve()
    scope = None
    if path != repo:
        try:
            scope = str(path.relative_to(repo))
        except ValueError:
            raise ActionError('Selected file is outside Git working tree')
    return repo, scope


def branch(repo: Path) -> str:
    return git(repo, 'symbolic-ref', '--quiet', '--short', 'HEAD', check=False) or '(detached HEAD)'


def stats(repo: Path) -> str:
    upstream = git(repo, 'rev-parse', '--abbrev-ref', '--symbolic-full-name', '@{upstream}', check=False)
    if not upstream:
        return 'Upstream: not configured'
    pair = git(repo, 'rev-list', '--left-right', '--count', 'HEAD...@{upstream}', check=False)
    parts = pair.split()
    if len(parts) == 2:
        return f'Upstream: {upstream} (ahead {parts[0]}, behind {parts[1]})'
    return f'Upstream: {upstream}'


def repo_github_url(repo: Path):
    origin = git(repo, 'remote', 'get-url', 'origin', check=False)
    if not origin:
        return None
    value = origin.strip()
    if value.startswith('git@github.com:'):
        repository = value.split(':', 1)[1]
    else:
        u = urlparse(value)
        if u.scheme not in ('https', 'ssh', 'git') or u.hostname != 'github.com':
            return None
        repository = u.path.lstrip('/')
    repository = (repository[:-4] if repository.endswith('.git') else repository).strip('/')
    if not re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+', repository):
        return None
    return 'https://github.com/' + repository


def notify(title: str, message: str, dialog: bool = False):
    if sys.platform != 'darwin':
        return
    # Escape AppleScript string literals without shell interpolation.
    def quote_as(value):
        return '"' + value.replace('\\', '\\\\').replace('"', '\\"').replace('\n', ' ') + '"'
    script = (f'display dialog {quote_as(message)} with title {quote_as(title)} buttons {{"OK"}} default button "OK"'
              if dialog else f'display notification {quote_as(message)} with title {quote_as(title)}')
    try:
        subprocess.run(['/usr/bin/osascript', '-e', script], stdout=subprocess.DEVNULL,
                       stderr=subprocess.DEVNULL, timeout=12, check=False)
    except (OSError, subprocess.TimeoutExpired):
        pass


def copy_to_clipboard(text: str):
    if sys.platform != 'darwin':
        print(text)
        return
    try:
        subprocess.run(['/usr/bin/pbcopy'], input=text.encode('utf-8'), check=True, timeout=10)
    except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
        raise ActionError(f'Failed copying to clipboard: {exc}') from exc


def open_url(url: str):
    if sys.platform != 'darwin':
        print(url)
        return
    try:
        subprocess.run(['/usr/bin/open', url], check=True, timeout=10)
    except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
        raise ActionError(f'Failed opening browser: {exc}') from exc


def status(repo: Path) -> str:
    sha = git(repo, 'rev-parse', '--short=12', 'HEAD', check=False) or '(no commits)'
    lines = [f'Repository: {repo.name}', f'Location: {repo}', f'Branch: {branch(repo)}',
             f'HEAD: {sha}', stats(repo), f'GitHub: {repo_github_url(repo) or "not configured"}',
             '', 'Working tree (including untracked files):']
    changes = git(repo, 'status', '--short', '--untracked-files=normal')
    lines.append(changes or '(clean)')
    return '\n'.join(lines) + '\n'


def show_status(repo: Path):
    content = status(repo)
    if sys.platform == 'darwin':
        cache = Path.home() / 'Library' / 'Caches' / 'git-finder-actions'
        cache.mkdir(parents=True, exist_ok=True)
        filename = hashlib.sha256(str(repo).encode()).hexdigest()[:12] + '.txt'
        output = cache / ('status-' + filename)
        output.write_text(content, encoding='utf-8')
        output.chmod(0o600)
        try:
            subprocess.run(['/usr/bin/open', '-a', 'TextEdit', str(output)], check=True, timeout=10)
        except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
            copy_to_clipboard(content)
            notify('Git Status', 'Status copied to clipboard (TextEdit could not open)')
    else:
        print(content, end='')


def copy_diff(repo: Path, scope):
    # Neither untracked file contents nor secrets are included automatically.
    pathspec = ['--', scope] if scope else []
    diff = git(repo, 'diff', '--no-ext-diff', '--no-color', '--no-textconv', 'HEAD', *pathspec)
    untracked = git(repo, 'ls-files', '--others', '--exclude-standard', *pathspec)
    result = (f'Git working diff — {repo.name} ({branch(repo)})\n'
              + (f'Scope: {scope}\n' if scope else 'Scope: whole repository\n')
              + f'Commit: {git(repo, "rev-parse", "HEAD", check=False)}\n\n'
              + (diff or '(no tracked changes)')
              + ('\n\nUntracked files (names only):\n' + untracked if untracked else '')
              + '\n')
    if len(result.encode('utf-8')) > MAX_DIFF_BYTES:
        raise ActionError('Diff is over 512 KB, not copied. Use git diff in Terminal instead.')
    copy_to_clipboard(result)
    notify('Git Copy Diff', f'Copied working diff from {repo.name}')


def copy_context(repo: Path):
    recent = git(repo, 'log', '-1', '--format=%h %s', check=False) or '(no commits)'
    result = status(repo) + f'Last commit: {recent}\n'
    copy_to_clipboard(result)
    notify('Git Copy Context', f'Copied context from {repo.name}')


def open_pr(repo: Path):
    url = repo_github_url(repo)
    if not url:
        raise ActionError('origin is not a github.com repository; cannot open GitHub PR')
    current = branch(repo)
    if current == '(detached HEAD)':
        open_url(url + '/pulls')
        return
    # When GitHub CLI is installed/authenticated, prefer the exact current-branch PR.
    gh = shutil.which('gh') or next((p for p in ['/opt/homebrew/bin/gh', '/usr/local/bin/gh'] if Path(p).exists()), None)
    if gh:
        try:
            proc = subprocess.run([gh, 'pr', 'view', current, '--json', 'url', '--jq', '.url'],
                                  cwd=str(repo), text=True, capture_output=True, timeout=12)
            candidate = proc.stdout.strip()
            if proc.returncode == 0 and candidate.startswith(url + '/pull/'):
                open_url(candidate)
                return
        except (OSError, subprocess.TimeoutExpired):
            pass
    # Safe fallback: PR list filtered to branch, not a fabricated PR link.
    open_url(url + '/pulls?q=' + quote(f'is:pr head:{current}', safe=''))
    notify('Git Open PR', 'Opened branch-filtered pull requests in GitHub')


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['status', 'copy-diff', 'open-pr', 'copy-context'])
    parser.add_argument('selection', nargs='+', help='One file or folder selected in Finder')
    args = parser.parse_args(argv)
    try:
        if len(args.selection) != 1:
            raise ActionError('Select exactly one file or folder in Finder')
        repo, scope = repo_for(args.selection[0])
        if args.action == 'status':
            show_status(repo)
        elif args.action == 'copy-diff':
            copy_diff(repo, scope)
        elif args.action == 'copy-context':
            copy_context(repo)
        else:
            open_pr(repo)
        return 0
    except ActionError as exc:
        print(f'Git Actions: {exc}', file=sys.stderr)
        notify('Git Actions', str(exc), dialog=True)
        return 1


if __name__ == '__main__':
    sys.exit(main())
