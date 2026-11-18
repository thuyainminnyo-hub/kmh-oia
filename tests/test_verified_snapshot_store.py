import hashlib
import os
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

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
            blob.write_bytes(b"x" * len(payload))
            with self.assertRaisesRegex(ValueError, "digest/size verification"):
                store.get_verified(reference)


    def test_rejects_snapshot_larger_than_policy_limit(self):
        with patch("src.verified_snapshot_store._MAX_SNAPSHOT_BYTES", 8):
            with tempfile.TemporaryDirectory() as tmp:
                store = VerifiedArtifactStore(Path(tmp) / "snapshots")
                payload = b"x" * 9
                with self.assertRaisesRegex(ValueError, "policy limit"):
                    store.put_bytes(
                        payload, artifact_id="job-too-large",
                        expected_sha256=hashlib.sha256(payload).hexdigest(),
                        expected_size_bytes=len(payload),
                    )

    def test_rejects_oversized_blob_on_retrieval_before_reading(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = VerifiedArtifactStore(Path(tmp) / "snapshots")
            payload = b"verified payload"
            reference = store.put_bytes(
                payload, artifact_id="job-oversized-read",
                expected_sha256=hashlib.sha256(payload).hexdigest(),
                expected_size_bytes=len(payload),
            )
            blob = store.root / reference.storage_key
            blob.chmod(0o644)
            blob.write_bytes(payload + b"x")
            with self.assertRaisesRegex(ValueError, "size mismatch"):
                store.get_verified(reference)

    def test_rejects_oversized_existing_blob_during_deduplication(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = VerifiedArtifactStore(Path(tmp) / "snapshots")
            payload = b"deduplicated payload"
            digest = hashlib.sha256(payload).hexdigest()
            first = store.put_bytes(
                payload, artifact_id="job-dedup-original",
                expected_sha256=digest, expected_size_bytes=len(payload),
            )
            blob = store.root / first.storage_key
            blob.chmod(0o644)
            blob.write_bytes(payload + b"x")
            with self.assertRaisesRegex(ValueError, "size mismatch"):
                store.put_bytes(
                    payload, artifact_id="job-dedup-retry",
                    expected_sha256=digest, expected_size_bytes=len(payload),
                )

    def test_rejects_truncated_blob_on_retrieval(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = VerifiedArtifactStore(Path(tmp) / "snapshots")
            payload = b"complete payload"
            reference = store.put_bytes(
                payload, artifact_id="job-truncated",
                expected_sha256=hashlib.sha256(payload).hexdigest(),
                expected_size_bytes=len(payload),
            )
            blob = store.root / reference.storage_key
            blob.chmod(0o644)
            blob.write_bytes(payload[:-1])
            with self.assertRaisesRegex(ValueError, "size mismatch"):
                store.get_verified(reference)

    def test_rejects_symlinked_intermediate_directory(self):
        if not hasattr(os, "symlink"):
            self.skipTest("symlinks are unavailable")
        with tempfile.TemporaryDirectory() as tmp:
            store = VerifiedArtifactStore(Path(tmp) / "snapshots")
            payload = b"intermediate symlink payload"
            reference = store.put_bytes(
                payload, artifact_id="job-parent-symlink",
                expected_sha256=hashlib.sha256(payload).hexdigest(),
                expected_size_bytes=len(payload),
            )
            first_dir = store.blob_root / reference.sha256[:2]
            outside = Path(tmp) / "outside"
            outside_blob = outside / reference.sha256[2:4] / reference.sha256
            outside_blob.parent.mkdir(parents=True)
            outside_blob.write_bytes(payload)
            shutil.rmtree(first_dir)
            try:
                os.symlink(outside, first_dir, target_is_directory=True)
            except (OSError, NotImplementedError):
                self.skipTest("directory symlinks are unavailable")
            with self.assertRaisesRegex(ValueError, "safely open"):
                store.get_verified(reference)

    def test_rejects_final_blob_symlink(self):
        if not hasattr(os, "symlink"):
            self.skipTest("symlinks are unavailable")
        with tempfile.TemporaryDirectory() as tmp:
            store = VerifiedArtifactStore(Path(tmp) / "snapshots")
            payload = b"final symlink payload"
            reference = store.put_bytes(
                payload, artifact_id="job-final-symlink",
                expected_sha256=hashlib.sha256(payload).hexdigest(),
                expected_size_bytes=len(payload),
            )
            blob = store.root / reference.storage_key
            outside = Path(tmp) / "outside.bin"
            outside.write_bytes(payload)
            blob.unlink()
            try:
                os.symlink(outside, blob)
            except (OSError, NotImplementedError):
                self.skipTest("file symlinks are unavailable")
            with self.assertRaisesRegex(ValueError, "safely open"):
                store.get_verified(reference)

    def test_rejects_non_regular_blob(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = VerifiedArtifactStore(Path(tmp) / "snapshots")
            payload = b"non regular payload"
            reference = store.put_bytes(
                payload, artifact_id="job-non-regular",
                expected_sha256=hashlib.sha256(payload).hexdigest(),
                expected_size_bytes=len(payload),
            )
            blob = store.root / reference.storage_key
            blob.unlink()
            blob.mkdir()
            with self.assertRaisesRegex(ValueError, "not a regular file"):
                store.get_verified(reference)

    def test_rejects_expected_size_mismatch_before_read(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = VerifiedArtifactStore(Path(tmp) / "snapshots")
            payload = b"expected-size payload"
            reference = store.put_bytes(
                payload, artifact_id="job-size-mismatch",
                expected_sha256=hashlib.sha256(payload).hexdigest(),
                expected_size_bytes=len(payload),
            )
            blob = store.root / reference.storage_key
            with self.assertRaisesRegex(ValueError, "size mismatch"):
                store._read_no_follow(
                    blob, expected_size=len(payload) + 1,
                    max_bytes=len(payload) + 1,
                )

    def test_enforces_byte_limit_if_blob_grows_after_open(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = VerifiedArtifactStore(Path(tmp) / "snapshots")
            payload = b"1234"
            reference = store.put_bytes(
                payload, artifact_id="job-growth-race",
                expected_sha256=hashlib.sha256(payload).hexdigest(),
                expected_size_bytes=len(payload),
            )
            blob = store.root / reference.storage_key
            blob.chmod(0o644)
            real_read = os.read
            grown = False

            def grow_then_read(fd, count):
                nonlocal grown
                if not grown:
                    grown = True
                    with blob.open("ab") as stream:
                        stream.write(b"56")
                return real_read(fd, count)

            with patch("src.verified_snapshot_store.os.read", side_effect=grow_then_read):
                with self.assertRaisesRegex(ValueError, "size limit"):
                    store._read_no_follow(
                        blob, expected_size=len(payload), max_bytes=len(payload),
                    )


if __name__ == "__main__":
    unittest.main()
