import hashlib
import os
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch

from src.verified_snapshot_store import VerifiedArtifactStore


class SnapshotPublicationSecurityTests(unittest.TestCase):
    def test_pub_01_temp_collision_is_not_removed_or_modified(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = VerifiedArtifactStore(Path(tmp) / "store")
            parent = store._open_directory(("artifacts",))
            name = ".item.json.tmp-fixed"
            try:
                fd = os.open(name, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600, dir_fd=parent)
                os.write(fd, b"attacker-owned")
                os.close(fd)
            finally:
                os.close(parent)
            with patch("src.verified_snapshot_store.secrets.token_hex", return_value="fixed"):
                with self.assertRaises(FileExistsError):
                    store._publish_file(("artifacts",), "item.json", b"safe", max_bytes=100)
            parent = store._open_directory(("artifacts",))
            try:
                fd = os.open(name, os.O_RDONLY, dir_fd=parent)
                try:
                    self.assertEqual(os.read(fd, 100), b"attacker-owned")
                finally:
                    os.close(fd)
            finally:
                os.close(parent)

    def test_pub_02_final_symlink_is_not_followed(self):
        if not hasattr(os, "symlink"):
            self.skipTest("symlinks unavailable")
        with tempfile.TemporaryDirectory() as tmp:
            store = VerifiedArtifactStore(Path(tmp) / "store")
            outside = Path(tmp) / "outside"
            outside.write_bytes(b"keep-me")
            parent = store._open_directory(("artifacts",))
            try:
                os.symlink(outside, "item.json", dir_fd=parent)
            except (OSError, NotImplementedError):
                os.close(parent)
                self.skipTest("symlink creation unavailable")
            os.close(parent)
            with self.assertRaises((ValueError, OSError)):
                store._publish_file(("artifacts",), "item.json", b"replacement", max_bytes=100)
            self.assertEqual(outside.read_bytes(), b"keep-me")

    def test_pub_03_destination_collision_never_overwrites(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = VerifiedArtifactStore(Path(tmp) / "store")
            parent = store._open_directory(("artifacts",))
            try:
                fd = os.open("item.json", os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600, dir_fd=parent)
                os.write(fd, b"original")
                os.close(fd)
            finally:
                os.close(parent)
            with self.assertRaisesRegex(ValueError, "byte-for-byte"):
                store._publish_file(("artifacts",), "item.json", b"original!", max_bytes=100)
            self.assertEqual((store.metadata_root / "item.json").read_bytes(), b"original")

    def test_pub_04_concurrent_same_digest_writers_are_idempotent(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = VerifiedArtifactStore(Path(tmp) / "store")
            payload = b"concurrent immutable bytes"
            digest = hashlib.sha256(payload).hexdigest()
            results, errors = [], []
            barrier = threading.Barrier(2)

            def writer(artifact_id):
                try:
                    barrier.wait()
                    results.append(store.put_bytes(payload, artifact_id=artifact_id,
                        expected_sha256=digest, expected_size_bytes=len(payload)))
                except Exception as exc:
                    errors.append(exc)

            threads = [threading.Thread(target=writer, args=(f"job-{i}",)) for i in range(2)]
            for thread in threads:
                thread.start()
            for thread in threads:
                thread.join()
            self.assertEqual(errors, [])
            self.assertEqual(len(results), 2)
            self.assertEqual((store.root / results[0].storage_key).read_bytes(), payload)

    def test_pub_05_pinned_directory_fd_survives_path_replacement(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = VerifiedArtifactStore(Path(tmp) / "store")
            real_link = os.link
            moved = Path(tmp) / "artifacts-original"
            replacement = Path(tmp) / "artifacts-replacement"

            def replace_then_link(src, dst, **kwargs):
                if not moved.exists():
                    store.metadata_root.rename(moved)
                    replacement.mkdir(mode=0o700)
                    store.metadata_root.mkdir(mode=0o700)
                return real_link(src, dst, **kwargs)

            with patch("src.verified_snapshot_store.os.link", side_effect=replace_then_link):
                store._publish_file(("artifacts",), "pinned.json", b"pinned", max_bytes=100)
            self.assertTrue((moved / "pinned.json").exists())
            self.assertFalse((replacement / "pinned.json").exists())

    def test_pub_06_metadata_uses_same_immutable_publication(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = VerifiedArtifactStore(Path(tmp) / "store")
            payload = b"metadata protected"
            digest = hashlib.sha256(payload).hexdigest()
            ref = store.put_bytes(payload, artifact_id="metadata-job",
                expected_sha256=digest, expected_size_bytes=len(payload))
            self.assertEqual(store.get_verified(ref), payload)
            self.assertEqual((store.metadata_root / "metadata-job.json").stat().st_mode & 0o777, 0o444)

    def test_pub_07_store_directories_are_private_to_service_uid(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "store"
            store = VerifiedArtifactStore(root)
            self.assertEqual(root.stat().st_uid, os.geteuid())
            self.assertEqual(root.stat().st_mode & 0o077, 0)
            self.assertEqual(store.blob_root.stat().st_mode & 0o077, 0)
            self.assertEqual(store.metadata_root.stat().st_mode & 0o077, 0)

    def test_pub_08_failed_publication_primitive_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = VerifiedArtifactStore(Path(tmp) / "store")
            with patch("src.verified_snapshot_store.os.link", side_effect=OSError("link unsupported")):
                with self.assertRaisesRegex(OSError, "link unsupported"):
                    store._publish_file(("artifacts",), "fail.json", b"x", max_bytes=10)
            self.assertFalse((store.metadata_root / "fail.json").exists())

    def test_pub_09_published_blob_digest_is_checked_on_read(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = VerifiedArtifactStore(Path(tmp) / "store")
            payload = b"verified digest"
            digest = hashlib.sha256(payload).hexdigest()
            ref = store.put_bytes(payload, artifact_id="digest-job",
                expected_sha256=digest, expected_size_bytes=len(payload))
            blob = store.root / ref.storage_key
            blob.chmod(0o644)
            blob.write_bytes(b"tampered digest")
            with self.assertRaisesRegex(ValueError, "digest/size verification"):
                store.get_verified(ref)

    def test_pub_10_metadata_failure_never_reports_a_committed_snapshot(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = VerifiedArtifactStore(Path(tmp) / "store")
            payload = b"crash boundary"
            digest = hashlib.sha256(payload).hexdigest()
            real_publish = store._publish_file

            def fail_metadata(parts, name, content, **kwargs):
                if parts == ("artifacts",):
                    raise OSError("injected crash before metadata publication")
                return real_publish(parts, name, content, **kwargs)

            with patch.object(store, "_publish_file", side_effect=fail_metadata):
                with self.assertRaisesRegex(OSError, "injected crash"):
                    store.put_bytes(payload, artifact_id="crash-job",
                        expected_sha256=digest, expected_size_bytes=len(payload))
            self.assertFalse((store.metadata_root / "crash-job.json").exists())


if __name__ == "__main__":
    unittest.main()
