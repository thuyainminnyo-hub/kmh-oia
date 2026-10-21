import hashlib
import tempfile
import unittest
from pathlib import Path

from src.runtime_artifact_measurement import (
    measure_artifact, normalize_sha256, require_artifact_digest, require_bytes_digest,
)


class RuntimeArtifactMeasurementTests(unittest.TestCase):
    def test_measured_file_digest_matches_content(self):
        content = b"classifier artifact bytes\n"
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "classifier.bin"
            path.write_bytes(content)
            artifact = measure_artifact(path)
            self.assertEqual(artifact.content, content)
            self.assertEqual(artifact.sha256, hashlib.sha256(content).hexdigest())

    def test_expected_digest_accepts_matching_file(self):
        content = b"policy artifact bytes\n"
        expected = hashlib.sha256(content).hexdigest()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "policy.bin"
            path.write_bytes(content)
            measured = require_artifact_digest(path, "sha256:" + expected)
            self.assertEqual(measured.sha256, expected)

    def test_changed_file_bytes_fail_closed(self):
        expected = hashlib.sha256(b"trusted bytes").hexdigest()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "classifier.bin"
            path.write_bytes(b"changed bytes")
            with self.assertRaisesRegex(ValueError, "SHA-256 mismatch"):
                require_artifact_digest(path, expected)

    def test_invalid_expected_digest_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "policy.bin"
            path.write_bytes(b"policy")
            with self.assertRaisesRegex(ValueError, "64 hexadecimal"):
                require_artifact_digest(path, "not-a-hash")

    def test_in_memory_bytes_are_checked_against_digest(self):
        content = b"loaded policy bytes"
        expected = hashlib.sha256(content).hexdigest()
        self.assertEqual(require_bytes_digest(content, expected, artifact_name="policy"), expected)
        with self.assertRaisesRegex(ValueError, "SHA-256 mismatch"):
            require_bytes_digest(b"modified bytes", expected, artifact_name="policy")

    def test_digest_normalization_rejects_non_hex(self):
        value = hashlib.sha256(b"x").hexdigest().upper()
        self.assertEqual(normalize_sha256("sha256:" + value), value.lower())
        with self.assertRaises(ValueError):
            normalize_sha256("g" * 64)


if __name__ == "__main__":
    unittest.main()
