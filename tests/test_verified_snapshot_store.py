import hashlib
from concurrent.futures import ThreadPoolExecutor
import tempfile
import unittest
from pathlib import Path

from src.verified_snapshot_store import VerifiedArtifactStore, VerifiedSnapshot


class VerifiedArtifactStoreTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.allowed = self.base / "outputs"
        self.allowed.mkdir()
        self.store = VerifiedArtifactStore(self.base / "snapshots")

    def write_source(self, name="image.bin", payload=b"verified-pixel-fixture"):
        path = self.allowed / name
        path.write_bytes(payload)
        return path

    def test_put_verified_stores_exact_bytes_and_returns_content_address(self):
        payload = b"verified-pixel-fixture" * 8192
        source = self.write_source(payload=payload)
        reference = self.store.put_verified(source, allowed_root=self.allowed, artifact_id="asset-001")

        self.assertEqual(reference.sha256, hashlib.sha256(payload).hexdigest())
        self.assertEqual(reference.size_bytes, len(payload))
        self.assertEqual(reference.storage_key, f"sha256/{reference.sha256[:2]}/{reference.sha256[2:4]}/{reference.sha256}")
        self.assertEqual(self.store.get_verified(reference), payload)

    def test_artifact_identity_is_separate_from_content_identity(self):
        source = self.write_source()
        first = self.store.put_verified(source, allowed_root=self.allowed, artifact_id="asset-a")
        second = self.store.put_verified(source, allowed_root=self.allowed, artifact_id="asset-b")

        self.assertNotEqual(first.artifact_id, second.artifact_id)
        self.assertEqual(first.sha256, second.sha256)
        self.assertEqual(first.storage_key, second.storage_key)

    def test_concurrent_ingestion_deduplicates_same_content(self):
        source = self.write_source(payload=b"same-content" * 1024)

        def ingest(index):
            return self.store.put_verified(
                source,
                allowed_root=self.allowed,
                artifact_id=f"parallel-{index}",
            )

        with ThreadPoolExecutor(max_workers=6) as pool:
            references = list(pool.map(ingest, range(6)))

        self.assertEqual(len({item.sha256 for item in references}), 1)
        self.assertEqual(len({item.storage_key for item in references}), 1)
        self.assertEqual(len(self.store.recover()), 6)

    def test_rejects_source_outside_allowed_root(self):
        outside = self.base / "outside.bin"
        outside.write_bytes(b"not allowed")
        with self.assertRaisesRegex(ValueError, "outside allowed_root"):
            self.store.put_verified(outside, allowed_root=self.allowed)

    def test_rejects_missing_source(self):
        with self.assertRaises(ValueError):
            self.store.put_verified(self.allowed / "missing.bin", allowed_root=self.allowed)

    def test_rejects_empty_source(self):
        source = self.write_source(payload=b"")
        with self.assertRaisesRegex(ValueError, "must not be empty"):
            self.store.put_verified(source, allowed_root=self.allowed)

    def test_refuses_to_overwrite_corrupt_existing_content_address(self):
        source = self.write_source(payload=b"immutable")
        reference = self.store.put_verified(source, allowed_root=self.allowed, artifact_id="first")
        blob = self.store.root / reference.storage_key
        blob.chmod(0o644)
        blob.write_bytes(b"corrupt")

        another_source = self.write_source("another.bin", b"immutable")
        with self.assertRaisesRegex(ValueError, "integrity verification"):
            self.store.put_verified(another_source, allowed_root=self.allowed, artifact_id="second")
        self.assertEqual(blob.read_bytes(), b"corrupt")

    def test_rejects_duplicate_artifact_identity(self):
        source = self.write_source()
        self.store.put_verified(source, allowed_root=self.allowed, artifact_id="same-id")
        with self.assertRaises(FileExistsError):
            self.store.put_verified(source, allowed_root=self.allowed, artifact_id="same-id")

    def test_rejects_tampered_blob_on_verify_and_read(self):
        source = self.write_source()
        reference = self.store.put_verified(source, allowed_root=self.allowed)
        blob = self.store.root / reference.storage_key
        blob.chmod(0o644)
        blob.write_bytes(b"tampered")
        with self.assertRaisesRegex(ValueError, "integrity verification"):
            self.store.verify(reference)
        with self.assertRaisesRegex(ValueError, "integrity verification"):
            self.store.get_verified(reference)

    def test_rejects_symlinked_blob(self):
        source = self.write_source(payload=b"original")
        reference = self.store.put_verified(source, allowed_root=self.allowed)
        blob = self.store.root / reference.storage_key
        blob.unlink()
        outside = self.base / "outside-blob.bin"
        outside.write_bytes(b"original")
        blob.symlink_to(outside)
        with self.assertRaisesRegex(ValueError, "symlink|safely open"):
            self.store.verify(reference)

    def test_rejects_symlinked_metadata(self):
        source = self.write_source(payload=b"original")
        reference = self.store.put_verified(source, allowed_root=self.allowed, artifact_id="symlink-meta")
        metadata = self.store.metadata_root / "symlink-meta.json"
        metadata.unlink()
        outside = self.base / "outside-meta.json"
        outside.write_text(
            __import__("json").dumps({
                "artifact_id": reference.artifact_id,
                "sha256": reference.sha256,
                "size_bytes": reference.size_bytes,
                "storage_key": reference.storage_key,
                "verification_version": reference.verification_version,
            }),
            encoding="utf-8",
        )
        metadata.symlink_to(outside)
        with self.assertRaisesRegex(ValueError, "symlink|safely open"):
            self.store.verify(reference)

    def test_rejects_metadata_substitution(self):
        source = self.write_source()
        reference = self.store.put_verified(source, allowed_root=self.allowed, artifact_id="asset-meta")
        metadata = self.store.metadata_root / "asset-meta.json"
        metadata.write_text('{"artifact_id":"asset-meta","sha256":"' + ("0" * 64) + '"}', encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "invalid snapshot metadata|does not match"):
            self.store.verify(reference)

    def test_recovery_returns_only_verified_metadata_records(self):
        first_source = self.write_source("one.bin", b"one")
        second_source = self.write_source("two.bin", b"two")
        first = self.store.put_verified(first_source, allowed_root=self.allowed, artifact_id="recover-one")
        second = self.store.put_verified(second_source, allowed_root=self.allowed, artifact_id="recover-two")

        second_blob = self.store.root / second.storage_key
        second_blob.chmod(0o644)
        second_blob.write_bytes(b"corrupted")

        recovered = self.store.recover()
        self.assertEqual(recovered, (first,))

    def test_rejects_forged_reference_with_wrong_storage_key(self):
        with self.assertRaisesRegex(ValueError, "does not match sha256"):
            VerifiedSnapshot(
                artifact_id="asset-forged",
                sha256="a" * 64,
                size_bytes=1,
                storage_key="sha256/not-the-digest",
            )

    def test_rejects_path_traversal_artifact_id(self):
        with self.assertRaisesRegex(ValueError, "safe identifier"):
            self.store.put_verified(
                self.write_source(),
                allowed_root=self.allowed,
                artifact_id="../escape",
            )


if __name__ == "__main__":
    unittest.main()
