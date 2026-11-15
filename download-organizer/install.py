#!/usr/bin/env python3
"""Install Download Organizer as a per-user macOS LaunchAgent."""
import os
import plistlib
import shutil
import subprocess
import sys
from pathlib import Path

LABEL = 'local.download-organizer'
HOME = Path.home()
HERE = Path(__file__).resolve().parent
APP_DIR = HOME / '.local' / 'share' / 'download-organizer'
CONFIG_DIR = HOME / '.config' / 'download-organizer'
STATE_DIR = HOME / '.local' / 'state' / 'download-organizer'
LOG_DIR = HOME / 'Library' / 'Logs'
PLIST = HOME / 'Library' / 'LaunchAgents' / f'{LABEL}.plist'
DOMAIN = f'gui/{os.getuid()}'


def call(*args, fail=True):
    return subprocess.run(list(args), check=fail, capture_output=True, text=True)


def main():
    if sys.platform != 'darwin':
        sys.exit('Installation requires macOS. The sorting script can run on other Unix systems.')
    for d in (APP_DIR, CONFIG_DIR, STATE_DIR, LOG_DIR, PLIST.parent):
        d.mkdir(parents=True, exist_ok=True)
    script = APP_DIR / 'download_organizer.py'
    config = CONFIG_DIR / 'config.json'
    state = STATE_DIR / 'state.json'
    shutil.copy2(HERE / 'download_organizer.py', script)
    if not config.exists():
        shutil.copy2(HERE / 'config.json', config)
        print(f'Created configuration: {config}')
    else:
        print(f'Preserved existing configuration: {config}')
    # Take a baseline before activating the agent: do not reorganize old downloads.
    if not state.exists():
        call(sys.executable, str(script), '--config', str(config), '--state', str(state), '--initialize')
    data = {
        'Label': LABEL,
        'ProgramArguments': [sys.executable, '-u', str(script), '--config', str(config), '--state', str(state)],
        'WatchPaths': [str(HOME / 'Downloads')],
        'StartInterval': 20,
        'RunAtLoad': True,
        'ProcessType': 'Background',
        'StandardOutPath': str(LOG_DIR / 'download-organizer.out.log'),
        'StandardErrorPath': str(LOG_DIR / 'download-organizer.err.log'),
    }
    # Unload before replacing the plist; bootout can fail on a first install.
    call('launchctl', 'bootout', DOMAIN, str(PLIST), fail=False)
    PLIST.write_bytes(plistlib.dumps(data, sort_keys=False))
    try:
        call('launchctl', 'bootstrap', DOMAIN, str(PLIST))
    except subprocess.CalledProcessError as exc:
        sys.exit(f'Could not start LaunchAgent:\n{exc.stderr}\nPlist: {PLIST}')
    print('Installed and enabled Download Organizer.')
    print('New downloads will be classified automatically after they settle (usually 20-40 seconds).')
    print(f'Config: {config}')
    print(f'Activity log: {LOG_DIR / "download-organizer.out.log"}')
    print('To view rules: open -e "' + str(config) + '"')


if __name__ == '__main__':
    main()
