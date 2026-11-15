from pathlib import Path
import plistlib
import subprocess
root = Path(__file__).resolve().parents[1]
for name in ('Print Selected Files', 'Preview Selected Files'):
    workflow = root / f'{name}.workflow' / 'Contents'
    info = plistlib.loads((workflow/'Info.plist').read_bytes())
    doc = plistlib.loads((workflow/'document.wflow').read_bytes())
    assert info['CFBundleName'] == name
    assert info['NSServices'][0]['NSMenuItem']['default'] == name
    assert doc['workflowMetaData']['serviceApplicationBundleID'] == 'com.apple.finder'
    act = doc['actions'][0]['action']
    assert act['ActionParameters']['inputMethod'] == 1
    cmd = act['ActionParameters']['COMMAND_STRING']
    assert 'print-selected-files.sh' in cmd
    assert '"$@"' in cmd
    if name.startswith('Preview'):
        assert '--preview' in cmd
    else:
        assert '--preview' not in cmd
for script in ['install.sh', 'uninstall.sh', 'print-selected-files.sh']:
    subprocess.run(['bash', '-n', str(root/script)], check=True)
script = (root/'print-selected-files.sh').read_text()
assert '/usr/bin/lp ' in script
assert 'MODE=print' in script
assert 'MODE=preview' in script
assert 'if [[ "$MODE" == preview ]]' in script
assert '/usr/bin/open -a Preview "$OUTPUT"' in script
assert '-- "$OUTPUT"' in script
subprocess.run(['node', '--check', str(root/'merge-pdf-images.js')], check=True)
print('Print/Preview workflow plists, shell, JXA and direct-print checks passed')
