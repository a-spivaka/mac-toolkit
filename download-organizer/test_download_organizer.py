"""Self-contained regression tests; run `python3 -m unittest discover -v`."""
import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from download_organizer import (
    eligible,
    execute,
    load_config,
    load_state,
    matching_rule,
)


class DownloadOrganizerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.downloads = self.root / 'Downloads'
        self.downloads.mkdir()
        self.state = self.root / 'state.json'
        self.config_path = self.root / 'config.json'
        self.config_path.write_text(json.dumps({
            'source_dir': str(self.downloads),
            'settle_seconds': 12,
            'rules': [
                {'name': 'Chizh', 'filename_globs': ['chizh-*'], 'extensions': ['.log'], 'destination': str(self.root / 'Chizh')},
                {'name': 'Docs', 'extensions': ['.pdf', '.doc', '.docx'], 'destination': str(self.root / 'Docs')},
                {'name': 'Images', 'extensions': ['.jpg', '.jpeg', '.png'], 'destination': str(self.root / 'Images')},
                {'name': 'Logs', 'extensions': ['.log'], 'destination': str(self.root / 'Logs')},
            ],
        }), encoding='utf-8')
        self.config = load_config(self.config_path)

    def run_execute(self, now=1000, **flags):
        with redirect_stdout(io.StringIO()) as stdout:
            result = execute(self.config, self.state, now=now, **flags)
        self.assertEqual(0, result)
        return stdout.getvalue()

    def test_extensions_and_globs_case_insensitive_and_first_match(self):
        rules = self.config['rules']
        self.assertEqual('Docs', matching_rule('Invoice.PDF', rules)['name'])
        self.assertEqual('Docs', matching_rule('paper.DOCX', rules)['name'])
        self.assertEqual('Images', matching_rule('IMG.JpG', rules)['name'])
        self.assertEqual('Chizh', matching_rule('CHIZH-123.LOG', rules)['name'])
        self.assertEqual('Logs', matching_rule('system.log', rules)['name'])
        self.assertIsNone(matching_rule('chizh-123.txt', rules))
        self.assertIsNone(matching_rule('unknown.zzz', rules))

    def test_baseline_does_not_move_old_files(self):
        old_file = self.downloads / 'old.pdf'
        old_file.write_text('old')
        self.run_execute(initialize=True)
        self.run_execute(now=2000)
        self.assertTrue(old_file.exists())
        self.assertFalse((self.root / 'Docs').exists())

    def test_new_download_waits_for_two_stable_observations(self):
        self.run_execute(initialize=True)
        pdf = self.downloads / 'new.pdf'
        pdf.write_text('content')
        self.assertIn('WAITING', self.run_execute(now=1000))
        self.assertTrue(pdf.exists())
        self.run_execute(now=1010)
        self.assertTrue(pdf.exists())
        self.assertIn('MOVED', self.run_execute(now=1013))
        self.assertFalse(pdf.exists())
        self.assertEqual('content', (self.root / 'Docs' / 'new.pdf').read_text())

    def test_changing_size_resets_stability_window(self):
        self.run_execute(initialize=True)
        f = self.downloads / 'big.pdf'
        f.write_text('first')
        self.run_execute(now=1000)
        f.write_text('updated')
        self.run_execute(now=1013)
        self.assertTrue(f.exists())
        self.run_execute(now=1020)
        self.assertTrue(f.exists())
        self.run_execute(now=1026)
        self.assertFalse(f.exists())
        self.assertEqual('updated', (self.root / 'Docs' / 'big.pdf').read_text())

    def test_collision_creates_numbered_copy_without_overwriting(self):
        self.run_execute(initialize=True)
        existing = self.root / 'Docs' / 'book.pdf'
        existing.parent.mkdir()
        existing.write_text('keep')
        f = self.downloads / 'book.pdf'
        f.write_text('fresh')
        self.run_execute(now=1000)
        self.run_execute(now=1013)
        self.assertEqual('keep', existing.read_text())
        self.assertEqual('fresh', (existing.parent / 'book (1).pdf').read_text())

    def test_dry_run_is_non_mutating_and_includes_existing_when_requested(self):
        f = self.downloads / 'manual.pdf'
        f.write_text('safe')
        preview = self.run_execute(now=1000, dry_run=True, include_existing=True, preview_now=True)
        self.assertIn('WOULD MOVE', preview)
        self.assertTrue(f.exists())
        self.assertFalse(self.state.exists())

    def test_skip_temporary_hidden_symlinks_folders(self):
        self.assertFalse(eligible(self.downloads / 'abc.crdownload'))
        (self.downloads / 'partial.pdf.crdownload').write_text('partial')
        (self.downloads / '.hidden.pdf').write_text('hidden')
        (self.downloads / 'folder.pdf').mkdir()
        (self.downloads / 'symlink.pdf').symlink_to(self.downloads / '.hidden.pdf')
        self.run_execute(initialize=True)
        self.assertEqual({}, load_state(self.state)['baseline'])

    def test_opt_in_existing_files(self):
        old_file = self.downloads / 'old.PDF'
        old_file.write_text('old')
        self.run_execute(initialize=True)
        self.run_execute(now=1000, include_existing=True)
        self.run_execute(now=1013, include_existing=True)
        self.assertTrue((self.root / 'Docs' / 'old.PDF').exists())

    def test_unmatched_files_stay_put(self):
        self.run_execute(initialize=True)
        f = self.downloads / 'unknown.txt'
        f.write_text('unknown')
        self.run_execute(now=1000)
        self.run_execute(now=1100)
        self.assertTrue(f.exists())


if __name__ == '__main__':
    unittest.main()
