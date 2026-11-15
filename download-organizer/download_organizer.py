#!/usr/bin/env python3
"""Sort completed files from a download folder according to configurable rules.

Standard library only. Designed to be invoked by a macOS launchd LaunchAgent.
"""
from __future__ import annotations

import argparse
import errno
import fnmatch
import json
import os
import sys
import time
from pathlib import Path
from typing import Any

import fcntl

DEFAULT_CONFIG = Path('~/.config/download-organizer/config.json').expanduser()
DEFAULT_STATE = Path('~/.local/state/download-organizer/state.json').expanduser()
TEMPORARY_EXTENSIONS = ('.crdownload', '.download', '.part', '.partial', '.tmp')


def expand_dir(value: str) -> Path:
    return Path(os.path.expandvars(os.path.expanduser(value))).resolve()


def load_config(path: Path) -> dict[str, Any]:
    with path.open(encoding='utf-8') as file:
        config = json.load(file)
    if not isinstance(config, dict):
        raise ValueError('Configuration must be a JSON object')
    source = config.get('source_dir', '~/Downloads')
    if not isinstance(source, str) or not source:
        raise ValueError('source_dir must be a nonempty string')
    config['source_dir'] = expand_dir(source)
    if not config['source_dir'].is_dir():
        raise ValueError(f"Source directory does not exist: {config['source_dir']}")

    settle = config.get('settle_seconds', 12)
    if isinstance(settle, bool) or not isinstance(settle, (int, float)) or settle < 0:
        raise ValueError('settle_seconds must be a nonnegative number')
    config['settle_seconds'] = float(settle)

    rules = config.get('rules')
    if not isinstance(rules, list):
        raise ValueError('rules must be a list')
    normalized = []
    for index, rule in enumerate(rules):
        if not isinstance(rule, dict):
            raise ValueError(f'rules[{index}] must be an object')
        if rule.get('enabled', True) is False:
            continue
        destination = rule.get('destination')
        if not isinstance(destination, str) or not destination:
            raise ValueError(f'rules[{index}].destination must be a nonempty string')
        extensions = rule.get('extensions', [])
        globs = rule.get('filename_globs', [])
        if not isinstance(extensions, list) or not all(isinstance(e, str) for e in extensions):
            raise ValueError(f'rules[{index}].extensions must be a list of strings')
        if not isinstance(globs, list) or not all(isinstance(e, str) for e in globs):
            raise ValueError(f'rules[{index}].filename_globs must be a list of strings')
        if not (extensions or globs):
            raise ValueError(f'rules[{index}] needs extensions or filename_globs')
        for ext in extensions:
            if not ext.startswith('.') or ext in ('.', '..'):
                raise ValueError(f'Invalid extension {ext!r}; use e.g. ".pdf"')
        dest_path = expand_dir(destination)
        if dest_path == config['source_dir']:
            raise ValueError(f'rules[{index}] destination cannot equal source_dir')
        normalized.append({
            'name': str(rule.get('name', f'Rule {index + 1}')),
            'destination': dest_path,
            'extensions': tuple(ext.casefold() for ext in extensions),
            'filename_globs': tuple(glob.casefold() for glob in globs),
        })
    config['rules'] = normalized
    return config


def eligible(path: Path) -> bool:
    # Only direct, visible, regular files. Never follow symbolic links.
    if path.name.startswith('.') or path.is_symlink() or not path.is_file():
        return False
    return not path.name.casefold().endswith(TEMPORARY_EXTENSIONS)


def fingerprint(path: Path) -> list[int]:
    s = path.stat()
    return [s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns, s.st_ctime_ns]


def current_files(source: Path) -> dict[str, tuple[Path, list[int]]]:
    out = {}
    for entry in source.iterdir():
        try:
            if eligible(entry):
                out[entry.name] = (entry, fingerprint(entry))
        except (FileNotFoundError, PermissionError):
            continue
    return out


def matching_rule(filename: str, rules: list[dict[str, Any]]) -> dict[str, Any] | None:
    lower = filename.casefold()
    for rule in rules:
        by_extension = bool(rule['extensions']) and any(lower.endswith(ext) for ext in rule['extensions'])
        by_name = bool(rule['filename_globs']) and any(fnmatch.fnmatchcase(lower, p) for p in rule['filename_globs'])
        # If both conditions are supplied, BOTH must match. Otherwise, match the supplied one.
        if (not rule['extensions'] or by_extension) and (not rule['filename_globs'] or by_name):
            return rule
    return None


def load_state(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    with path.open(encoding='utf-8') as file:
        state = json.load(file)
    if state.get('version') != 1:
        raise ValueError(f'Unsupported state file version in {path}')
    return state


def save_state(path: Path, state: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + '.tmp')
    with temp.open('w', encoding='utf-8') as file:
        json.dump(state, file, indent=2, sort_keys=True)
        file.write('\n')
        file.flush()
        os.fsync(file.fileno())
    os.replace(temp, path)


def new_state(files: dict[str, tuple[Path, list[int]]]) -> dict[str, Any]:
    return {
        'version': 1,
        'baseline': {name: signature for name, (_, signature) in files.items()},
        'pending': {},
    }


def split_name(filename: str) -> tuple[str, str]:
    """Preserve compound archive extensions when adding conflict suffixes."""
    lower = filename.casefold()
    for ext in ('.tar.gz', '.tar.bz2', '.tar.xz'):
        if lower.endswith(ext):
            return filename[:-len(ext)], filename[-len(ext):]
    p = Path(filename)
    return filename[:-len(p.suffix)] if p.suffix else filename, p.suffix


def move_without_overwriting(source: Path, destination_folder: Path) -> Path:
    """Safely create the target without ever replacing an existing file.

    Uses a hard link then unlink for files on the same filesystem. Cross-volume
    destinations are copied to a new exclusive target before deleting source.
    """
    destination_folder.mkdir(parents=True, exist_ok=True)
    stem, suffix = split_name(source.name)
    for number in range(10000):
        candidate = destination_folder / (source.name if number == 0 else f'{stem} ({number}){suffix}')
        try:
            os.link(source, candidate, follow_symlinks=False)
        except FileExistsError:
            continue
        except OSError as exc:
            if exc.errno != errno.EXDEV:
                raise
            # Exclusive creation prevents overwrites, even on a different disk.
            try:
                out_fd = os.open(candidate, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            except FileExistsError:
                continue
            try:
                import shutil
                with os.fdopen(out_fd, 'wb') as dst, source.open('rb') as src:
                    shutil.copyfileobj(src, dst)
                    dst.flush()
                    os.fsync(dst.fileno())
                shutil.copystat(source, candidate)
            except BaseException:
                candidate.unlink(missing_ok=True)
                raise
        try:
            source.unlink()
        except Exception:
            # Do not remove destination: source and destination now contain the same file.
            # Surfacing this error lets the operator resolve unusual permissions/races.
            raise
        return candidate
    raise RuntimeError(f'Too many naming collisions for {source.name}')


def execute(config: dict[str, Any], state_path: Path, *, initialize: bool = False,
            dry_run: bool = False, include_existing: bool = False,
            preview_now: bool = False, now: float | None = None) -> int:
    now = time.time() if now is None else now
    files = current_files(config['source_dir'])
    if initialize:
        if state_path.exists():
            print(f'Existing state preserved: {state_path}')
            return 0
        save_state(state_path, new_state(files))
        print(f'Initialized: {len(files)} existing files excluded from future automatic moves.')
        return 0

    state = load_state(state_path)
    if state is None:
        if dry_run:
            state = new_state(files)
        else:
            # Safety: existing files are never reorganized on first run.
            state = new_state(files)
            save_state(state_path, state)
            print(f'First run: left {len(files)} existing files untouched.')
            return 0

    changed = False
    baseline = state['baseline']
    pending = state['pending']
    for old_name in list(baseline):
        if old_name not in files or files[old_name][1] != baseline[old_name]:
            del baseline[old_name]
            changed = True
    for old_name in list(pending):
        if old_name not in files:
            del pending[old_name]
            changed = True

    moved = 0
    for name, (file_path, sig) in sorted(files.items()):
        if not include_existing and baseline.get(name) == sig:
            continue
        rule = matching_rule(name, config['rules'])
        if rule is None:
            if name in pending:
                del pending[name]
                changed = True
            continue
        dest_dir = rule['destination']
        if dry_run and preview_now:
            print(f'WOULD MOVE [{rule["name"]}]: {file_path} -> {dest_dir / name}')
            moved += 1
            continue

        observation = pending.get(name)
        if observation is None or observation['signature'] != sig:
            if not dry_run:
                pending[name] = {'signature': sig, 'first_seen': now}
                changed = True
            print(f'WAITING (checking download completed): {name}')
            continue
        elapsed = now - observation['first_seen']
        if elapsed < config['settle_seconds']:
            print(f'WAITING ({config["settle_seconds"] - elapsed:.0f}s): {name}')
            continue
        # Recheck immediately before movement to catch concurrent Chrome writes.
        try:
            if not eligible(file_path) or fingerprint(file_path) != sig:
                if not dry_run:
                    pending.pop(name, None)
                    changed = True
                continue
        except FileNotFoundError:
            continue
        if dry_run:
            print(f'WOULD MOVE [{rule["name"]}]: {file_path} -> {dest_dir / name}')
        else:
            try:
                target = move_without_overwriting(file_path, dest_dir)
            except Exception as exc:
                print(f'ERROR moving {file_path}: {exc}', file=sys.stderr)
                continue
            print(f'MOVED [{rule["name"]}]: {file_path} -> {target}')
            pending.pop(name, None)
            changed = True
        moved += 1

    if changed and not dry_run:
        save_state(state_path, state)
    if dry_run:
        print(f'Preview: {moved} matching file(s). No changes were made.')
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, default=DEFAULT_CONFIG)
    parser.add_argument('--state', type=Path, default=DEFAULT_STATE)
    parser.add_argument('--initialize', action='store_true', help='Keep all current downloads untouched')
    parser.add_argument('--dry-run', action='store_true', help='Preview, do not move or update state')
    parser.add_argument('--all', action='store_true', help='Also consider downloads that predate installation')
    parser.add_argument('--now', action='store_true', help='Only with --dry-run: ignore settle time')
    args = parser.parse_args(argv)
    if args.now and not args.dry_run:
        parser.error('--now is only permitted with --dry-run')
    try:
        config = load_config(args.config.expanduser())
        args.state = args.state.expanduser()
        args.state.parent.mkdir(parents=True, exist_ok=True)
        lock = args.state.with_suffix('.lock')
        with lock.open('a+') as lock_file:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            return execute(config, args.state, initialize=args.initialize,
                           dry_run=args.dry_run, include_existing=args.all,
                           preview_now=args.now)
    except BlockingIOError:
        # Another invocation is already sorting downloads.
        return 0
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f'ERROR: {exc}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
