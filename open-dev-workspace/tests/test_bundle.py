#!/usr/bin/env python3
from pathlib import Path
import plistlib
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
BUNDLE = ROOT / 'Open Development Workspace.workflow' / 'Contents'
SCRIPT = ROOT / 'open-workspace.sh'


def test_plists():
    info = plistlib.loads((BUNDLE / 'Info.plist').read_bytes())
    wflow = plistlib.loads((BUNDLE / 'document.wflow').read_bytes())
    assert info['CFBundleIdentifier'] == 'dev.chizh.open-development-workspace'
    assert info['NSServices'][0]['NSSendFileTypes'] == ['public.folder']
    assert wflow['workflowMetaData']['serviceApplicationBundleID'] == 'com.apple.finder'
    action = wflow['actions'][0]['action']
    assert action['ActionName'] == 'Run Shell Script'
    assert action['ActionParameters']['inputMethod'] == 1
    assert '"$@"' in action['ActionParameters']['COMMAND_STRING']


def run(*args):
    return subprocess.run(list(args), stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)


def test_script():
    assert run('bash', '-n', str(SCRIPT)).returncode == 0
    assert run('bash', str(SCRIPT), '--dry-run', '/nonexistent-folder').returncode != 0
    with tempfile.TemporaryDirectory(prefix='workspace-test-') as tmp:
        root = Path(tmp) / 'Repo With Spaces'
        root.mkdir()
        nested = root / 'sub folder'
        nested.mkdir()
        assert run('git', 'init', '-q', str(root)).returncode == 0
        assert run('git', '-C', str(root), 'config', 'user.name', 'Tester').returncode == 0
        assert run('git', '-C', str(root), 'config', 'user.email', 'test@example.invalid').returncode == 0
        (root / 'a.txt').write_text('test\n')
        assert run('git', '-C', str(root), 'add', 'a.txt').returncode == 0
        assert run('git', '-C', str(root), 'commit', '-qm', 'init').returncode == 0
        assert run('git', '-C', str(root), 'remote', 'add', 'origin', 'git@github.com:example/test-repo.git').returncode == 0
        (root / 'a.txt').write_text('changed\n')
        (root / 'new.txt').write_text('new\n')
        result = run('bash', str(SCRIPT), '--dry-run', str(nested))
        assert result.returncode == 0, result.stderr
        assert f'Repository: {root}' in result.stdout
        assert 'Changed files: 2' in result.stdout
        assert 'no tracking upstream' in result.stdout
        assert 'GitHub: https://github.com/example/test-repo' in result.stdout
        assert 'Dry run: did not open any apps.' in result.stdout
        assert run('git', '-C', str(root), 'remote', 'set-url', 'origin', 'https://evil.example/test').returncode == 0
        result2 = run('bash', str(SCRIPT), '--dry-run', str(root))
        assert 'GitHub: not configured' in result2.stdout
        assert 'evil.example' not in result2.stdout
        assert run('git', '-C', str(root), 'remote', 'set-url', 'origin', 'https://username:secret@github.com/example/test-repo.git').returncode == 0
        result3 = run('bash', str(SCRIPT), '--dry-run', str(root))
        assert 'GitHub: not configured' in result3.stdout
        assert 'secret' not in result3.stdout

if __name__ == '__main__':
    test_plists()
    test_script()
    print('PASS: workflow properties, shell syntax, repo detection, paths with spaces, count, URL validation')
