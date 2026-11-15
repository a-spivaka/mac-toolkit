#!/usr/bin/env python3
"""Add a Media rule to an installed Download Organizer config, preserving custom rules."""
from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import tempfile
from datetime import datetime
from pathlib import Path

EXTENSIONS = (
    '.mp4', '.mov', '.m4v', '.mkv', '.avi', '.webm', '.wmv', '.mpg',
    '.mpeg', '.3gp', '.m2ts',
    '.mp3', '.m4a', '.aac', '.wav', '.flac', '.ogg', '.opus', '.aiff',
)
DEFAULT_CONFIG = Path('~/.config/download-organizer/config.json').expanduser()
DESTINATION = '~/Downloads/Media'


def update(path: Path) -> str:
    if not path.is_file():
        raise FileNotFoundError(f'Config not found: {path}. Install Download Organizer first.')
    with path.open('r', encoding='utf-8') as fh:
        config = json.load(fh)
    if not isinstance(config, dict) or not isinstance(config.get('rules'), list):
        raise ValueError('Unexpected config format: expected a JSON object with a rules array')
    rules = config['rules']
    if any(not isinstance(rule, dict) for rule in rules):
        raise ValueError('Unexpected config format: each rule must be an object')

    # Prefer existing Media rule or same destination, retain user-defined destination.
    existing = next((r for r in rules if r.get('name', '').casefold() == 'media'), None)
    if existing is None:
        existing = next((r for r in rules if r.get('destination') == DESTINATION), None)

    if existing is not None:
        exts = existing.get('extensions', [])
        if not isinstance(exts, list) or not all(isinstance(x, str) for x in exts):
            raise ValueError('Media rule extensions is not a list of strings')
        seen = {x.casefold() for x in exts}
        exts.extend(x for x in EXTENSIONS if x not in seen)
        existing['extensions'] = exts
        # No filename_globs: the Media rule should match all of these extensions.
        if existing.get('filename_globs'):
            raise ValueError('Existing Media rule has filename_globs; edit it manually to avoid changing intent')
        if existing.get('enabled') is False:
            existing['enabled'] = True
        dest = existing.get('destination', DESTINATION)
        outcome = 'Updated existing Media rule'
    else:
        new_rule = {'name': 'Media', 'extensions': list(EXTENSIONS), 'destination': DESTINATION}
        insert_before = next((i for i, r in enumerate(rules) if r.get('name') in {'Archives', 'Installers', 'Other logs'}), len(rules))
        rules.insert(insert_before, new_rule)
        dest = DESTINATION
        outcome = 'Added Media rule'

    # Only write if the configuration actually changed.
    original_text = path.read_text(encoding='utf-8')
    output_text = json.dumps(config, indent=2, ensure_ascii=False) + '\n'
    if json.loads(original_text) == config:
        print('Already configured; no changes needed.')
    else:
        backup = path.with_name(path.name + '.backup-' + datetime.now().strftime('%Y%m%d-%H%M%S'))
        # Avoid clobbering earlier backups even on rapid retries.
        backup_candidate = backup
        index = 1
        while backup_candidate.exists():
            backup_candidate = path.with_name(backup.name + '-' + str(index))
            index += 1
        shutil.copy2(path, backup_candidate)
        fd, tmp = tempfile.mkstemp(prefix='.config-media-', suffix='.json', dir=str(path.parent))
        try:
            os.fchmod(fd, path.stat().st_mode & 0o777)
            with os.fdopen(fd, 'w', encoding='utf-8') as out:
                out.write(output_text)
                out.flush()
                os.fsync(out.fileno())
            os.replace(tmp, path)
        finally:
            if os.path.exists(tmp):
                os.unlink(tmp)
        print(f'{outcome}. Backup: {backup_candidate}')
    directory = Path(os.path.expandvars(os.path.expanduser(dest)))
    directory.mkdir(parents=True, exist_ok=True)
    print(f'Destination: {directory}')
    print('New media downloads will be routed automatically. Existing media files may also move if they were downloaded after the organizer was first installed.')
    return str(directory)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, default=DEFAULT_CONFIG,
                        help='Config JSON path (default: ~/.config/download-organizer/config.json)')
    args = parser.parse_args()
    try:
        update(args.config.expanduser())
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f'ERROR: {exc}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
