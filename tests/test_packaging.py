import contextlib
import io
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import build


class PackageTests(unittest.TestCase):
    def test_reproducible_archive_has_only_authored_release_output(self):
        model=build.load()
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            with patch.object(build,'ROOT',root),patch.object(build,'OUT',root/'generated'),contextlib.redirect_stdout(io.StringIO()):
                build.build();build.package()
                path=root/f"dist/telluric-horizons-{model['version']}.zip"
                first=path.read_bytes();build.package();self.assertEqual(first,path.read_bytes())
                with zipfile.ZipFile(path) as archive:
                    self.assertIsNone(archive.testzip())
                    actual={n:archive.read(n) for n in archive.namelist()}
                    self.assertEqual(actual,build.render(model))
                    self.assertFalse(any('/events/' in n or 'th_test' in n or n.endswith(('.sav','.so','.acf','.dds')) for n in actual))


if __name__=='__main__':unittest.main()
