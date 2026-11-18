import hashlib
import tempfile
import unittest
from pathlib import Path

from src.verified_snapshot_store import VerifiedArtifactStore


class VerifiedArtifactStoreTests(unittest.TestCase):
    def test_stores_and_retrieves_exact_verified_bytes(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = VerifiedArtifactStore(Path(tmp) / "snapshots")
            payload = b"verified png bytes"
            digest = hashlib.sha256(payload).hexdigest()
            reference = store.put_bytes(
                payload, artifact_id="job-one",
                expected_sha256=digest, expected_size_bytes=len(payload),
            )
            self.assertEqual(reference.sha256, digest)
            self.assertEqual(reference.size_bytes, len(payload))
            self.assertEqual(store.get_verified(reference), payload)

    def test_rejects_payload_digest_mismatch_before_publication(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = VerifiedArtifactStore(Path(tmp) / "snapshots")
            payload = b"original"
            with self.assertRaisesRegex(ValueError, "does not match PNG integrity"):
                store.put_bytes(
                    b"substituted", artifact_id="job-mismatch",
                    expected_sha256=hashlib.sha256(payload).hexdigest(),
                    expected_size_bytes=len(payload),
                )
            self.assertFalse((store.metadata_root / "job-mismatch.json").exists())

    def test_rejects_mutated_snapshot_on_retrieval(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = VerifiedArtifactStore(Path(tmp) / "snapshots")
            payload = b"immutable original"
            reference = store.put_bytes(
                payload, artifact_id="job-tamper",
                expected_sha256=hashlib.sha256(payload).hexdigest(),
                expected_size_bytes=len(payload),
            )
            blob = store.root / reference.storage_key
            blob.chmod(0o644)
            blob.write_bytes(b"tampered")
            with self.assertRaisesRegex(ValueError, "digest/size verification"):
                store.get_verified(reference)


if __name__ == "__main__":
    unittest.main()
