import hashlib
import json
from pathlib import Path
import plistlib
import subprocess
import sys
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'bundle.py'
CONFIG = json.loads((ROOT / 'config.json').read_text())


class BundleTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.out = self.root / 'bundles'
        self.config_path = self.root / 'config.json'
        self.settings = dict(CONFIG, output_directory=str(self.out))
        self.set_config()

    def set_config(self):
        self.config_path.write_text(json.dumps(self.settings))

    def run_bundle(self, *args, options=()):
        return subprocess.run([sys.executable, str(SCRIPT), '--config', str(self.config_path),
                               *options, *(str(a) for a in args)], capture_output=True, text=True)

    def make(self, name, contents=b'hello'):
        p = self.root / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(contents)
        return p

    def bundles(self):
        return list(self.out.glob('*.zip')) if self.out.exists() else []

    def test_bundle_manifest_and_hashes(self):
        a = self.make('app.log', b'log line\n')
        b = self.make('response.json', b'{"ok": true}\n')
        result = self.run_bundle(a, b)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(len(self.bundles()), 1)
        with zipfile.ZipFile(self.bundles()[0]) as zf:
            manifest = json.loads(zf.read('manifest.json'))
            self.assertEqual(manifest['file_count'], 2)
            self.assertEqual(manifest['schema_version'], 1)
            self.assertEqual(zf.read('files/001/app.log'), a.read_bytes())
            self.assertEqual(zf.read('files/002/response.json'), b.read_bytes())
            self.assertEqual(manifest['files'][0]['sha256'], hashlib.sha256(a.read_bytes()).hexdigest())
            self.assertNotIn(str(self.root), json.dumps(manifest))
            self.assertIn(b'NOT scanned', zf.read('README.txt'))
        self.assertEqual(a.read_bytes(), b'log line\n')

    def test_duplicate_names_from_different_directories(self):
        a = self.make('one/log.txt', b'1')
        b = self.make('two/log.txt', b'2')
        result = self.run_bundle(a, b)
        self.assertEqual(result.returncode, 0, result.stderr)
        with zipfile.ZipFile(self.bundles()[0]) as zf:
            self.assertEqual(zf.read('files/001/log.txt'), b'1')
            self.assertEqual(zf.read('files/002/log.txt'), b'2')

    def test_dry_run_never_creates_output(self):
        a = self.make('hello log.log')
        result = self.run_bundle(a, options=('--dry-run',))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('DRY RUN', result.stdout)
        self.assertFalse(self.out.exists())

    def test_reject_folders_without_creating_archive(self):
        result = self.run_bundle(self.root)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('regular files', result.stderr)
        self.assertFalse(self.bundles())

    def test_reject_symlinks_without_creating_archive(self):
        src = self.make('source.txt')
        link = self.root / 'link.txt'
        link.symlink_to(src)
        result = self.run_bundle(link)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('symlinks', result.stderr)
        self.assertFalse(self.bundles())

    def test_reject_secrets_without_creating_archive(self):
        a = self.make('okay.log')
        for name in ('.env', '.env.production', 'id_rsa', 'private-key.pem', 'credentials.json'):
            b = self.make(name, b'fake secret')
            result = self.run_bundle(a, b)
            self.assertNotEqual(result.returncode, 0, name)
            self.assertIn('blocked', result.stderr)
            self.assertFalse(self.bundles())

    def test_file_size_limit_is_all_or_nothing(self):
        self.settings['max_file_mb'] = 1
        self.set_config()
        small = self.make('small.log')
        large = self.make('large.bin', b'x' * (1024 * 1024 + 1))
        result = self.run_bundle(small, large)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('exceeds', result.stderr)
        self.assertFalse(self.bundles())

    def test_total_limit_is_all_or_nothing(self):
        self.settings['max_total_mb'] = 1
        self.set_config()
        a = self.make('a.bin', b'x' * 700_000)
        b = self.make('b.bin', b'y' * 700_000)
        result = self.run_bundle(a, b)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('total limit', result.stderr)
        self.assertFalse(self.bundles())

    def test_does_not_overwrite_existing_zip(self):
        a = self.make('log.txt')
        one = self.run_bundle(a)
        two = self.run_bundle(a)
        self.assertEqual(one.returncode, 0, one.stderr)
        self.assertEqual(two.returncode, 0, two.stderr)
        self.assertEqual(len(self.bundles()), 2)

    def test_unicode_and_weird_filename(self):
        a = self.make('לוג with spaces 🐈.txt', b'123')
        result = self.run_bundle(a)
        self.assertEqual(result.returncode, 0, result.stderr)
        with zipfile.ZipFile(self.bundles()[0]) as zf:
            self.assertEqual(zf.read('files/001/' + a.name), b'123')

    def test_no_inputs(self):
        result = self.run_bundle()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('Select one or more', result.stderr)

    def test_invalid_config(self):
        self.settings['max_files'] = 'twenty'
        self.set_config()
        a = self.make('log.txt')
        result = self.run_bundle(a)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('max_files', result.stderr)

    def test_workflow_is_finder_action_with_argument_input(self):
        cont = ROOT / 'Prepare Debug Bundle.workflow' / 'Contents'
        with (cont / 'Info.plist').open('rb') as f:
            info = plistlib.load(f)
        with (cont / 'document.wflow').open('rb') as f:
            workflow = plistlib.load(f)
        self.assertEqual(info['NSServices'][0]['NSSendFileTypes'], ['public.item'])
        self.assertEqual(workflow['actions'][0]['action']['ActionParameters']['inputMethod'], 1)
        self.assertIn('"$@"', workflow['actions'][0]['action']['ActionParameters']['COMMAND_STRING'])


if __name__ == '__main__':
    unittest.main()
