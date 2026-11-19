"""Regression coverage for the cache-link failure seen on TACC."""
import errno
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import qwen_backbone_timing as timing


class CacheReuseTests(unittest.TestCase):
    def test_rejected_links_copy_exact_bytes_and_preserve_source(self):
        for code in [errno.EPERM, errno.EACCES, errno.EXDEV, errno.EOPNOTSUPP]:
            with self.subTest(errno=code), tempfile.TemporaryDirectory() as directory:
                source = Path(directory) / 'source'
                target = Path(directory) / 'target'
                source.write_bytes(b'frozen model bytes\x00\xff')
                before = timing.digest(source)
                with patch.object(timing.os, 'link', side_effect=OSError(code, 'blocked')):
                    timing.reuse_model_file(source, target)
                self.assertEqual(timing.digest(target), before)
                self.assertEqual(timing.digest(source), before)
                self.assertNotEqual(source.stat().st_ino, target.stat().st_ino)
                self.assertFalse(target.with_name('target.copy-part').exists())

    def test_unrelated_link_error_is_not_hidden(self):
        with patch.object(timing.os, 'link', side_effect=OSError(errno.ENOSPC, 'full')):
            with self.assertRaises(OSError) as caught:
                timing.reuse_model_file(Path('source'), Path('target'))
        self.assertEqual(caught.exception.errno, errno.ENOSPC)

    def test_failed_copy_does_not_publish_partial_file(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / 'source'
            target = Path(directory) / 'target'
            source.write_bytes(b'frozen')

            def interrupted_copy(original, partial):
                partial.write_bytes(b'fro')
                raise OSError(errno.ENOSPC, 'full')

            with patch.object(timing.os, 'link', side_effect=OSError(errno.EPERM, 'blocked')):
                with patch.object(timing.shutil, 'copyfile', side_effect=interrupted_copy):
                    with self.assertRaises(OSError):
                        timing.reuse_model_file(source, target)
            self.assertFalse(target.exists())
            self.assertFalse(target.with_name('target.copy-part').exists())
            self.assertEqual(source.read_bytes(), b'frozen')


if __name__ == '__main__':
    unittest.main()
