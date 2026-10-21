import gzip
import io
import json
import tarfile
import tempfile
import unittest
from pathlib import Path

from scripts.package_runtime_bundle import build_runtime_bundle
from scripts.validate_runtime_bundle import validate_runtime_bundle

class RuntimeBundlePackageTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / 'src').mkdir()
        (self.root / 'src' / 'runtime.py').write_text('VALUE = 1\n', encoding='utf-8')
        (self.root / 'src' / 'nested').mkdir()
        (self.root / 'src' / 'nested' / 'helper.py').write_text('def run(): return True\n', encoding='utf-8')
        (self.root / 'requirements.txt').write_text('cryptography==50.0.2\n', encoding='utf-8')
        self.revision = 'a' * 40

    def test_build_is_deterministic_and_manifest_bound(self):
        first = build_runtime_bundle(self.root, self.revision, self.root / 'one.tar.gz')
        second = build_runtime_bundle(self.root, self.revision, self.root / 'two.tar.gz')
        self.assertEqual(first.read_bytes(), second.read_bytes())
        result = validate_runtime_bundle(first, expected_source_sha=self.revision)
        self.assertEqual(result['files_verified'], 3)

    def test_mismatched_revision_and_empty_bundle_fail_closed(self):
        bundle = build_runtime_bundle(self.root, self.revision, self.root / 'bundle.tar.gz')
        with self.assertRaisesRegex(ValueError, 'does not match expected source SHA'):
            validate_runtime_bundle(bundle, expected_source_sha='b' * 40)
        empty = self.root / 'empty.tar.gz'
        empty.write_bytes(b'')
        with self.assertRaisesRegex(ValueError, 'must not be empty'):
            validate_runtime_bundle(empty, expected_source_sha=self.revision)

    def test_tampered_file_bytes_fail_manifest_check(self):
        bundle = build_runtime_bundle(self.root, self.revision, self.root / 'bundle.tar.gz')
        with tarfile.open(bundle, 'r:gz') as archive:
            members = {m.name: archive.extractfile(m).read() for m in archive.getmembers()}
        members['kmh-oia-runtime-source/src/runtime.py'] = b'VALUE = 999\n'
        tar_bytes = io.BytesIO()
        with tarfile.open(fileobj=tar_bytes, mode='w:gz') as archive:
            for name, data in members.items():
                info = tarfile.TarInfo(name); info.size = len(data); archive.addfile(info, io.BytesIO(data))
        tampered = self.root / 'tampered.tar.gz'
        tampered.write_bytes(tar_bytes.getvalue())
        with self.assertRaisesRegex(ValueError, 'manifest SHA-256 mismatch'):
            validate_runtime_bundle(tampered, expected_source_sha=self.revision)

    def test_malformed_tar_and_output_overwrite_are_rejected(self):
        output = build_runtime_bundle(self.root, self.revision, self.root / 'bundle.tar.gz')
        with self.assertRaisesRegex(ValueError, 'refusing to overwrite'):
            build_runtime_bundle(self.root, self.revision, output)
        (self.root / 'bad.tar.gz').write_bytes(b'not a tar')
        with self.assertRaisesRegex(ValueError, 'invalid gzip/tar'):
            validate_runtime_bundle(self.root / 'bad.tar.gz', expected_source_sha=self.revision)

if __name__ == '__main__':
    unittest.main()
