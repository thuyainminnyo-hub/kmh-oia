import gzip
import hashlib
import io
import tarfile
import tempfile
import unittest
from pathlib import Path

from scripts.package_runtime_bundle import build_runtime_bundle
from scripts.validate_runtime_bundle import validate_runtime_bundle

class RuntimeBundlePackagingSecurityTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / 'src').mkdir()
        (self.root / 'src' / 'runtime.py').write_text('VALUE = 1\n', encoding='utf-8')
        (self.root / 'requirements.txt').write_text('cryptography==50.0.2\n', encoding='utf-8')
        self.revision = 'a' * 40

    def test_bundle_is_byte_for_byte_deterministic_and_manifest_bound(self):
        first, second = self.root / 'first.tar.gz', self.root / 'second.tar.gz'
        build_runtime_bundle(self.root, self.revision, first)
        build_runtime_bundle(self.root, self.revision, second)
        self.assertEqual(first.read_bytes(), second.read_bytes())
        result = validate_runtime_bundle(first, expected_source_sha=self.revision)
        self.assertEqual(result['bundle_sha256'], hashlib.sha256(first.read_bytes()).hexdigest())
        self.assertGreaterEqual(result['files_verified'], 2)

    def test_packager_rejects_symlinked_runtime_source(self):
        outside = self.root / 'outside.py'
        outside.write_text('SECRET = True\n', encoding='utf-8')
        (self.root / 'src' / 'linked.py').symlink_to(outside)
        with self.assertRaisesRegex(ValueError, 'symlinks are not allowed'):
            build_runtime_bundle(self.root, self.revision, self.root / 'unsafe.tar.gz')

    def test_validator_rejects_duplicate_archive_entries(self):
        bundle = self.root / 'duplicate.tar.gz'
        with bundle.open('wb') as raw, gzip.GzipFile(filename='', mode='wb', fileobj=raw, mtime=0) as compressed:
            with tarfile.open(fileobj=compressed, mode='w') as archive:
                for _ in range(2):
                    info = tarfile.TarInfo('kmh-oia-runtime-source/src/runtime.py')
                    info.size = 1
                    archive.addfile(info, io.BytesIO(b'x'))
        with self.assertRaisesRegex(ValueError, 'duplicate archive paths'):
            validate_runtime_bundle(bundle, expected_source_sha=self.revision)

    def test_validator_rejects_archive_path_escape(self):
        bundle = self.root / 'escape.tar.gz'
        with bundle.open('wb') as raw, gzip.GzipFile(filename='', mode='wb', fileobj=raw, mtime=0) as compressed:
            with tarfile.open(fileobj=compressed, mode='w') as archive:
                info = tarfile.TarInfo('../escape.txt')
                info.size = 1
                archive.addfile(info, io.BytesIO(b'x'))
        with self.assertRaisesRegex(ValueError, 'unsafe or unexpected archive path'):
            validate_runtime_bundle(bundle, expected_source_sha=self.revision)

    def test_packager_refuses_to_overwrite_existing_bundle(self):
        target = self.root / 'output.tar.gz'
        target.write_bytes(b'existing artifact')
        with self.assertRaisesRegex(ValueError, 'refusing to overwrite'):
            build_runtime_bundle(self.root, self.revision, target)

if __name__ == '__main__':
    unittest.main()
