import importlib.util
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest import mock

MODULE = Path(__file__).resolve().parents[1] / 'git_actions.py'
spec = importlib.util.spec_from_file_location('git_actions', MODULE)
g = importlib.util.module_from_spec(spec)
spec.loader.exec_module(g)


def cmd(repo, *args):
    subprocess.run(['git', '-C', str(repo), *args], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


class GitActionsTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name) / 'a project'
        self.root.mkdir()
        cmd(self.root, 'init', '-q')
        cmd(self.root, 'config', 'user.name', 'Example')
        cmd(self.root, 'config', 'user.email', 'example@example.invalid')
        (self.root / 'hello world.txt').write_text('before\n')
        cmd(self.root, 'add', '.')
        cmd(self.root, 'commit', '-qm', 'Initial')
        cmd(self.root, 'remote', 'add', 'origin', 'git@github.com:a-spivaka/chizh.git')

    def test_find_repo_from_selected_file(self):
        repo, scope = g.repo_for(str(self.root / 'hello world.txt'))
        self.assertEqual(repo, self.root)
        self.assertEqual(scope, 'hello world.txt')
        sub = self.root / 'nested folder'
        sub.mkdir()
        repo, scope = g.repo_for(str(sub))
        self.assertEqual((repo, scope), (self.root, 'nested folder'))

    def test_status_and_origin_parse(self):
        self.assertEqual(g.repo_github_url(self.root), 'https://github.com/a-spivaka/chizh')
        self.assertIn('Upstream: not configured', g.status(self.root))
        self.assertIn('(clean)', g.status(self.root))
        cmd(self.root, 'remote', 'set-url', 'origin', 'https://evil.com/example/malware')
        self.assertIsNone(g.repo_github_url(self.root))

    def test_copy_diff_and_untracked(self):
        (self.root / 'hello world.txt').write_text('after\n')
        (self.root / 'new file.txt').write_text('untracked content\n')
        with mock.patch.object(g, 'copy_to_clipboard') as clipboard, mock.patch.object(g, 'notify'):
            g.copy_diff(self.root, None)
        text = clipboard.call_args[0][0]
        self.assertIn('+after', text)
        self.assertIn('new file.txt', text)
        self.assertNotIn('untracked content', text)
        # Read-only; working tree still dirty and file contents unchanged.
        self.assertEqual((self.root / 'hello world.txt').read_text(), 'after\n')

    def test_scope_and_size_limit(self):
        (self.root / 'hello world.txt').write_text('updated\n')
        nested = self.root / 'docs'
        nested.mkdir()
        (nested / 'sample').write_text('foo')
        with mock.patch.object(g, 'copy_to_clipboard') as clip, mock.patch.object(g, 'notify'):
            g.copy_diff(self.root, 'docs')
        self.assertIn('no tracked changes', clip.call_args[0][0])
        with mock.patch.object(g, 'MAX_DIFF_BYTES', 1):
            with self.assertRaises(g.ActionError):
                g.copy_diff(self.root, None)

    def test_open_pr_fallback_filter(self):
        with mock.patch.object(g.shutil, 'which', return_value=None), \
             mock.patch.object(g.Path, 'exists', return_value=False), \
             mock.patch.object(g, 'open_url') as open_url, \
             mock.patch.object(g, 'notify'):
            g.open_pr(self.root)
        self.assertIn('/pulls?q=', open_url.call_args[0][0])
        self.assertIn('head%3A', open_url.call_args[0][0])

    def test_copy_context(self):
        with mock.patch.object(g, 'copy_to_clipboard') as clip, mock.patch.object(g, 'notify'):
            g.copy_context(self.root)
        self.assertIn('Last commit:', clip.call_args[0][0])


if __name__ == '__main__':
    unittest.main()
