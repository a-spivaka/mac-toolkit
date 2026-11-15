#!/usr/bin/env python3
"""Build a bounded, read-only ZIP of Finder-selected regular files.

No third-party packages, network calls, directory recursion or secret-content scans.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
import secrets
import stat
import subprocess
import sys
import tempfile
import time
import zipfile

CHUNK = 1024 * 1024
DEFAULT_CONFIG = Path('~/.config/prepare-debug-bundle/config.json').expanduser()
NOTICE = 'Contents are NOT scanned for secrets. Review the ZIP before sharing.'


class BundleError(Exception):
    pass


def load_config(config_path: Path) -> dict:
    try:
        with config_path.open(encoding='utf-8') as fp:
            config = json.load(fp)
    except (OSError, json.JSONDecodeError) as exc:
        raise BundleError(f'Cannot read config {config_path}: {exc}') from exc
    if not isinstance(config, dict):
        raise BundleError('Configuration must be a JSON object.')
    for key in ('max_files', 'max_file_mb', 'max_total_mb'):
        value = config.get(key)
        if type(value) is not int or value <= 0:
            raise BundleError(f'{key} must be a positive integer.')
    output = config.get('output_directory')
    if not isinstance(output, str) or not output.strip():
        raise BundleError('output_directory must be a non-empty string.')
    output_path = Path(output).expanduser()
    if not output_path.is_absolute():
        raise BundleError('output_directory must be an absolute path (or start with ~/).')
    config['output_path'] = output_path
    for key in ('blocked_extensions', 'blocked_filename_regex'):
        values = config.get(key)
        if not isinstance(values, list) or not all(isinstance(v, str) for v in values):
            raise BundleError(f'{key} must be a list of strings.')
    try:
        config['blocked_patterns'] = [re.compile(expr, re.IGNORECASE) for expr in config['blocked_filename_regex']]
    except re.error as exc:
        raise BundleError(f'Invalid blocked_filename_regex: {exc}') from exc
    return config


def safe_archive_name(filename: str) -> str:
    """Preserve the readable name while preventing ZIP path components or controls."""
    cleaned = ''.join('_' if (ord(ch) < 32 or ch in '/\\') else ch for ch in filename)
    if cleaned in ('', '.', '..'):
        raise BundleError(f'Unsafe filename: {filename!r}')
    return cleaned


def source_metadata(path: Path, config: dict):
    try:
        info = path.lstat()
    except OSError as exc:
        raise BundleError(f'Cannot access {path}: {exc}') from exc
    if not stat.S_ISREG(info.st_mode):
        raise BundleError(f'Only regular files are supported (not folders or symlinks): {path.name}')
    if path.suffix.lower() in {s.lower() for s in config['blocked_extensions']} or any(
        p.search(path.name) for p in config['blocked_patterns']
    ):
        raise BundleError(f'Sensitive-looking filename is blocked: {path.name}')
    if info.st_size > config['max_file_mb'] * 1024 * 1024:
        raise BundleError(f'File exceeds {config["max_file_mb"]} MiB limit: {path.name}')
    return info


def validate_selection(args: list[str], config: dict) -> list[tuple[Path, os.stat_result]]:
    if not args:
        raise BundleError('Select one or more files in Finder first.')
    if len(args) > config['max_files']:
        raise BundleError(f'Too many selected files (maximum {config["max_files"]}).')
    seen = set()
    sources = []
    total = 0
    for raw in args:
        path = Path(raw).expanduser().absolute()
        if path in seen:
            continue
        seen.add(path)
        info = source_metadata(path, config)
        total += info.st_size
        if total > config['max_total_mb'] * 1024 * 1024:
            raise BundleError(f'Selection exceeds {config["max_total_mb"]} MiB total limit.')
        sources.append((path, info))
    if not sources:
        raise BundleError('No regular files selected.')
    return sources


def still_same_file(before: os.stat_result, after: os.stat_result) -> bool:
    return (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns) == (
        after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns
    )


def stream_to_zip(zf: zipfile.ZipFile, source: Path, initial: os.stat_result, arcname: str,
                  max_file_bytes: int) -> tuple[int, str]:
    flags = os.O_RDONLY | getattr(os, 'O_NOFOLLOW', 0)
    try:
        fd = os.open(source, flags)
    except OSError as exc:
        raise BundleError(f'Cannot open {source.name}: {exc}') from exc
    try:
        with os.fdopen(fd, 'rb') as src:
            fd = -1
            opened = os.fstat(src.fileno())
            if not stat.S_ISREG(opened.st_mode) or not still_same_file(initial, opened):
                raise BundleError(f'File changed after selection: {source.name}')
            safe_time = max(time.localtime(opened.st_mtime)[:6], (1980, 1, 1, 0, 0, 0))
            zi = zipfile.ZipInfo(arcname, date_time=safe_time)
            zi.compress_type = zipfile.ZIP_DEFLATED
            zi.external_attr = 0o100644 << 16
            size = 0
            digest = hashlib.sha256()
            with zf.open(zi, 'w', force_zip64=True) as output:
                while True:
                    chunk = src.read(CHUNK)
                    if not chunk:
                        break
                    size += len(chunk)
                    if size > max_file_bytes or size > initial.st_size:
                        raise BundleError(f'File grew while archiving: {source.name}')
                    output.write(chunk)
                    digest.update(chunk)
            # Check descriptor AND original directory entry to detect replacement/modification.
            try:
                current = source.lstat()
            except OSError as exc:
                raise BundleError(f'File changed or disappeared: {source.name}') from exc
            if size != initial.st_size or not still_same_file(initial, os.fstat(src.fileno())) or not still_same_file(initial, current):
                raise BundleError(f'File changed while archiving: {source.name}')
            return size, digest.hexdigest()
    finally:
        if fd >= 0:
            os.close(fd)


def build_bundle(sources: list[tuple[Path, os.stat_result]], config: dict, dry_run: bool) -> Path | None:
    dest = config['output_path']
    planned_size = sum(s.st_size for _, s in sources)
    if dry_run:
        print(f'DRY RUN: would create a ZIP in {dest}')
        for index, (path, info) in enumerate(sources, 1):
            print(f'  files/{index:03d}/{safe_archive_name(path.name)} ({info.st_size} bytes)')
        print(f'Total input: {planned_size} bytes; no files created.')
        return None

    try:
        dest.mkdir(parents=True, exist_ok=True, mode=0o700)
        if not dest.is_dir():
            raise BundleError(f'Output is not a directory: {dest}')
    except OSError as exc:
        raise BundleError(f'Cannot create output directory {dest}: {exc}') from exc

    fd, temp_name = tempfile.mkstemp(prefix='.debug-bundle-', suffix='.zip', dir=dest)
    os.close(fd)
    temporary = Path(temp_name)
    now = dt.datetime.now(dt.timezone.utc)
    published = None
    try:
        manifest = {
            'schema_version': 1,
            'created_at_utc': now.isoformat(timespec='seconds'),
            'file_count': len(sources),
            'warning': NOTICE,
            'files': [],
        }
        with zipfile.ZipFile(temporary, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=6,
                             allowZip64=True) as zf:
            zf.writestr('README.txt', 'Prepare Debug Bundle\n\n' + NOTICE + '\n\nFile names inside files/ are prefixed with selection numbers.\n')
            for index, (source, info) in enumerate(sources, 1):
                arcname = f'files/{index:03d}/{safe_archive_name(source.name)}'
                bytes_written, sha = stream_to_zip(zf, source, info, arcname,
                                                  config['max_file_mb'] * 1024 * 1024)
                manifest['files'].append({
                    'filename': source.name,
                    'archive_path': arcname,
                    'size_bytes': bytes_written,
                    'sha256': sha,
                    'modified_at_utc': dt.datetime.fromtimestamp(info.st_mtime, dt.timezone.utc).isoformat(timespec='seconds'),
                })
            zf.writestr('manifest.json', json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')

        name = 'debug-bundle-' + now.astimezone().strftime('%Y%m%d-%H%M%S') + '-' + secrets.token_hex(4) + '.zip'
        published = dest / name
        # Hardlink creates the final name atomically, and refuses to overwrite an existing name.
        os.link(temporary, published)
        return published
    except (OSError, zipfile.BadZipFile) as exc:
        raise BundleError(f'Could not create archive: {exc}') from exc
    finally:
        temporary.unlink(missing_ok=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description='Create a safe, bounded debug ZIP from selected files.')
    parser.add_argument('--config', type=Path, default=DEFAULT_CONFIG, help='JSON config path')
    parser.add_argument('--dry-run', action='store_true', help='Preview without writing a ZIP')
    parser.add_argument('--reveal', action='store_true', help='Reveal the finished ZIP in Finder (macOS)')
    parser.add_argument('files', nargs='*', help='One or more regular files (not directories)')
    args = parser.parse_args(argv)
    try:
        config = load_config(args.config.expanduser())
        sources = validate_selection(args.files, config)
        result = build_bundle(sources, config, args.dry_run)
        if result is not None:
            print(f'Created: {result}')
            if args.reveal and sys.platform == 'darwin':
                subprocess.run(['/usr/bin/open', '-R', str(result)], check=False)
        return 0
    except BundleError as exc:
        print(f'Prepare Debug Bundle: {exc}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
