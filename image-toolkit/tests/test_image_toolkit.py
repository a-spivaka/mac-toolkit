import os
from pathlib import Path
import subprocess
import tempfile
import unittest

BASE = Path(__file__).resolve().parents[1]
SCRIPT = BASE / 'image-toolkit.sh'


class ImageToolkitTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.dir = Path(self.tmp.name)
        self.fake = self.dir / 'fake-sips'
        self.fake.write_text('''#!/bin/bash
set -e
if [[ "$1" == "-g" ]]; then exit 0; fi
src=""; out=""
for (( i=1; i<=$#; i++ )); do
  val="${!i}"
  if [[ "$val" == "--out" ]]; then j=$((i+1)); out="${!j}"; fi
done
[[ -n "$out" ]] || exit 9
printf 'transformed' > "$out"
''')
        self.fake.chmod(0o755)

    def call(self, mode, *paths):
        return subprocess.run(['bash', str(SCRIPT), mode, *(str(p) for p in paths)],
                              text=True, capture_output=True,
                              env={**os.environ, 'SIPS_BIN': str(self.fake)})

    def test_copy_and_deduplicate(self):
        original = self.dir / 'my photo.HEIC'
        original.write_text('original')
        r = self.call('jpeg', original)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual((self.dir / 'my photo_jpeg.jpg').read_text(), 'transformed')
        r2 = self.call('jpeg', original)
        self.assertEqual(r2.returncode, 0, r2.stderr)
        self.assertTrue((self.dir / 'my photo_jpeg (1).jpg').exists())
        self.assertEqual(original.read_text(), 'original')

    def test_batch_and_resize(self):
        a = self.dir / 'one.png'; b = self.dir / 'two.jpeg'
        a.write_text('1'); b.write_text('2')
        r = self.call('resize1600', a, b)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertTrue((self.dir / 'one_1600.png').exists())
        self.assertTrue((self.dir / 'two_1600.jpeg').exists())
        self.assertEqual(a.read_text(), '1')

    def test_skip_symlink(self):
        a = self.dir / 'first.png'; a.write_text('original')
        link = self.dir / 'alias.png'; link.symlink_to(a)
        r = self.call('png', link)
        self.assertNotEqual(r.returncode, 0)
        self.assertFalse((self.dir / 'alias_png.png').exists())


if __name__ == '__main__':
    unittest.main()
