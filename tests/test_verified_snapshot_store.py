import hashlib
import multiprocessing
import os
import shutil
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
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

    def test_rejects_symlinked_staging_directory_during_publication(self):
        if not hasattr(os, "symlink"):
            self.skipTest("symlinks are unavailable")
        with tempfile.TemporaryDirectory() as tmp:
            store = VerifiedArtifactStore(Path(tmp) / "snapshots")
            outside = Path(tmp) / "outside"
            outside.mkdir()
            store.staging_root.rmdir()
            os.symlink(outside, store.staging_root, target_is_directory=True)
            payload = b"write path staging symlink"
            with self.assertRaises((ValueError, OSError, RuntimeError)):
                store.put_bytes(
                    payload, artifact_id="staging-symlink",
                    expected_sha256=hashlib.sha256(payload).hexdigest(),
                    expected_size_bytes=len(payload),
                )
            self.assertEqual(list(outside.iterdir()), [])

    def test_rejects_symlinked_metadata_directory_during_publication(self):
        if not hasattr(os, "symlink"):
            self.skipTest("symlinks are unavailable")
        with tempfile.TemporaryDirectory() as tmp:
            store = VerifiedArtifactStore(Path(tmp) / "snapshots")
            outside = Path(tmp) / "outside-metadata"
            outside.mkdir()
            store.metadata_root.rmdir()
            os.symlink(outside, store.metadata_root, target_is_directory=True)
            payload = b"metadata directory substitution"
            with self.assertRaises((ValueError, OSError, RuntimeError)):
                store.put_bytes(
                    payload, artifact_id="metadata-symlink",
                    expected_sha256=hashlib.sha256(payload).hexdigest(),
                    expected_size_bytes=len(payload),
                )
            self.assertEqual(list(outside.iterdir()), [])

    def test_rejects_symlinked_blob_destination_during_publication(self):
        if not hasattr(os, "symlink"):
            self.skipTest("symlinks are unavailable")
        with tempfile.TemporaryDirectory() as tmp:
            store = VerifiedArtifactStore(Path(tmp) / "snapshots")
            outside = Path(tmp) / "outside-blobs"
            outside.mkdir()
            payload = b"blob destination substitution"
            digest = hashlib.sha256(payload).hexdigest()
            first_level = store.blob_root / digest[:2]
            first_level.symlink_to(outside, target_is_directory=True)
            with self.assertRaises((ValueError, OSError, RuntimeError)):
                store.put_bytes(
                    payload, artifact_id="blob-parent-symlink",
                    expected_sha256=digest, expected_size_bytes=len(payload),
                )
            self.assertEqual(list(outside.rglob("*")), [])

    def test_fails_closed_without_no_follow_hard_link_support(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = VerifiedArtifactStore(Path(tmp) / "snapshots")
            payload = b"capability guard"
            with patch("src.verified_snapshot_store.os.supports_follow_symlinks", set()):
                with self.assertRaisesRegex(RuntimeError, "no-follow snapshot hard-link"):
                    store.put_bytes(
                        payload, artifact_id="unsupported-link",
                        expected_sha256=hashlib.sha256(payload).hexdigest(),
                        expected_size_bytes=len(payload),
                    )
            self.assertFalse((store.metadata_root / "unsupported-link.json").exists())

    def test_metadata_publication_failure_does_not_admit_snapshot(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = VerifiedArtifactStore(Path(tmp) / "snapshots")
            payload = b"metadata failure after blob publication"
            digest = hashlib.sha256(payload).hexdigest()
            original_open = os.open

            def fail_metadata_open(path, flags, *args, **kwargs):
                if path == "artifacts" and kwargs.get("dir_fd") is not None:
                    raise PermissionError("injected metadata directory failure")
                return original_open(path, flags, *args, **kwargs)

            # The mock replaces os.open's identity; preserve its advertised
            # dir_fd capability while injecting the targeted metadata failure.
            with patch("src.verified_snapshot_store.os.open", side_effect=fail_metadata_open) as mocked_open:
                with patch("src.verified_snapshot_store.os.supports_dir_fd", os.supports_dir_fd | {mocked_open}):
                    with self.assertRaisesRegex(PermissionError, "injected metadata"):
                        store.put_bytes(
                            payload, artifact_id="metadata-failure",
                            expected_sha256=digest, expected_size_bytes=len(payload),
                        )
            self.assertFalse((store.metadata_root / "metadata-failure.json").exists())
            self.assertEqual(list(store.staging_root.iterdir()), [])
            # A content-addressed orphan may exist; it must not be admitted as evidence.
            self.assertEqual((store.blob_root / digest[:2] / digest[2:4] / digest).read_bytes(), payload)

    def test_rejects_replaced_store_root_ancestor_symlink_on_publication(self):
        if not hasattr(os, "symlink"):
            self.skipTest("symlinks are unavailable")
        with tempfile.TemporaryDirectory() as tmp:
            parent = Path(tmp) / "trusted-parent"
            parent.mkdir()
            store = VerifiedArtifactStore(parent / "snapshots")
            displaced = Path(tmp) / "displaced-parent"
            parent.rename(displaced)
            outside = Path(tmp) / "outside-parent"
            outside.mkdir()
            shutil.copytree(displaced / "snapshots", outside / "snapshots")
            parent.symlink_to(outside, target_is_directory=True)
            payload = b"ancestor symlink substitution"
            with self.assertRaises((ValueError, OSError, RuntimeError)):
                store.put_bytes(
                    payload, artifact_id="ancestor-substitution",
                    expected_sha256=hashlib.sha256(payload).hexdigest(),
                    expected_size_bytes=len(payload),
                )
            self.assertEqual(
                list((outside / "snapshots" / "artifacts").iterdir()), []
            )

    def test_republished_artifact_verifies_only_pinned_entries(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = VerifiedArtifactStore(Path(tmp) / "snapshots")
            payload = b"pinned existing blob and metadata"
            digest = hashlib.sha256(payload).hexdigest()
            original = store.put_bytes(
                payload, artifact_id="job-pinned-reuse",
                expected_sha256=digest, expected_size_bytes=len(payload),
            )
            # Reusing an artifact must not re-open the mutable pathname.
            with patch.object(
                store, "_read_no_follow",
                side_effect=AssertionError("mutable pathname reopened during publication"),
            ):
                repeated = store.put_bytes(
                    payload, artifact_id="job-pinned-reuse",
                    expected_sha256=digest, expected_size_bytes=len(payload),
                )
            self.assertEqual(repeated, original)

    def test_root_replacement_during_deduplication_stays_on_pinned_store(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = VerifiedArtifactStore(Path(tmp) / "snapshots")
            payload = b"unchanged data from pinned parent directory"
            digest = hashlib.sha256(payload).hexdigest()
            original = store.put_bytes(
                payload, artifact_id="job-pinned-root",
                expected_sha256=digest, expected_size_bytes=len(payload),
            )
            displaced_root = Path(tmp) / "original-snapshot-root"
            saved_read = store._read_pinned_entry
            replaced = False

            def swap_then_read(*args, **kwargs):
                nonlocal replaced
                if not replaced:
                    replaced = True
                    store.root.rename(displaced_root)
                    store.root.mkdir()
                    impostor = store.root / original.storage_key
                    impostor.parent.mkdir(parents=True)
                    impostor.write_bytes(b"substituted pathname blob")
                    (store.root / "artifacts").mkdir()
                return saved_read(*args, **kwargs)

            with patch.object(store, "_read_pinned_entry", side_effect=swap_then_read):
                repeated = store.put_bytes(
                    payload, artifact_id="job-pinned-root",
                    expected_sha256=digest, expected_size_bytes=len(payload),
                )
            self.assertTrue(replaced)
            self.assertEqual(repeated, original)
            self.assertEqual(
                (displaced_root / original.storage_key).read_bytes(), payload
            )
            self.assertTrue(
                (displaced_root / "artifacts" / "job-pinned-root.json").exists()
            )
            self.assertEqual(list((store.root / "artifacts").iterdir()), [])

    def test_deduplication_rejects_symlinked_blob_entry(self):
        if not hasattr(os, "symlink"):
            self.skipTest("symlinks are unavailable")
        with tempfile.TemporaryDirectory() as tmp:
            store = VerifiedArtifactStore(Path(tmp) / "snapshots")
            payload = b"cannot reuse a symlinked blob"
            digest = hashlib.sha256(payload).hexdigest()
            original = store.put_bytes(
                payload, artifact_id="job-original-symlink-test",
                expected_sha256=digest, expected_size_bytes=len(payload),
            )
            outside = Path(tmp) / "outside-original.bin"
            outside.write_bytes(payload)
            blob = store.root / original.storage_key
            blob.unlink()
            blob.symlink_to(outside)
            with self.assertRaisesRegex(ValueError, "safely read published"):
                store.put_bytes(
                    payload, artifact_id="job-reused-symlink-test",
                    expected_sha256=digest, expected_size_bytes=len(payload),
                )
            self.assertFalse(
                (store.metadata_root / "job-reused-symlink-test.json").exists()
            )

    def test_rejects_group_or_world_writable_store_directories(self):
        if os.name != "posix" or not hasattr(os, "geteuid"):
            self.skipTest("POSIX directory ownership policy only")
        for directory_name in ("root", "blob_root", "staging_root", "metadata_root"):
            with self.subTest(directory=directory_name):
                with tempfile.TemporaryDirectory() as tmp:
                    store = VerifiedArtifactStore(Path(tmp) / "snapshots")
                    target = getattr(store, directory_name)
                    original_mode = target.stat().st_mode & 0o7777
                    try:
                        target.chmod(original_mode | 0o022)
                        payload = b"untrusted directory permissions"
                        with self.assertRaisesRegex(
                            (PermissionError, RuntimeError), "store directory|writable"
                        ):
                            store.put_bytes(
                                payload, artifact_id="untrusted-dir",
                                expected_sha256=hashlib.sha256(payload).hexdigest(),
                                expected_size_bytes=len(payload),
                            )
                    finally:
                        target.chmod(original_mode)
                    self.assertFalse(
                        (store.metadata_root / "untrusted-dir.json").exists()
                    )

    def test_deduplication_retries_after_hardlink_count_changes(self):
        # Unlinking an extra hard link modifies ctime, not file contents.
        # The collision reader should retry against the same pinned parent.
        with tempfile.TemporaryDirectory() as tmp:
            store = VerifiedArtifactStore(Path(tmp) / "snapshots")
            payload = b"content survives benign hard-link count changes"
            digest = hashlib.sha256(payload).hexdigest()
            first = store.put_bytes(
                payload, artifact_id="ctime-original",
                expected_sha256=digest, expected_size_bytes=len(payload),
            )
            blob = store.root / first.storage_key
            extra_link = blob.parent / "extra-hardlink"
            os.link(blob, extra_link)
            original_read = os.read
            unlinked = False

            def unlink_while_reading(fd, count):
                nonlocal unlinked
                if not unlinked:
                    unlinked = True
                    extra_link.unlink()
                return original_read(fd, count)

            with patch("src.verified_snapshot_store.os.read", side_effect=unlink_while_reading):
                repeated = store.put_bytes(
                    payload, artifact_id="ctime-reused",
                    expected_sha256=digest, expected_size_bytes=len(payload),
                )
            self.assertTrue(unlinked)
            self.assertFalse(extra_link.exists())
            self.assertEqual(repeated.sha256, first.sha256)
            self.assertEqual(store.get_verified(repeated), payload)

    def test_multiprocess_identical_publication_preserves_single_record(self):
        if "fork" not in multiprocessing.get_all_start_methods():
            self.skipTest("multiprocess fork test requires POSIX fork")
        with tempfile.TemporaryDirectory() as tmp:
            store = VerifiedArtifactStore(Path(tmp) / "snapshots")
            payload = b"same verified payload from independent worker processes"
            digest = hashlib.sha256(payload).hexdigest()
            context = multiprocessing.get_context("fork")
            start = context.Barrier(4)
            outcomes = context.Queue()

            def publish():
                try:
                    start.wait(timeout=15)
                    for _ in range(3):
                        reference = VerifiedArtifactStore(store.root).put_bytes(
                            payload, artifact_id="multiprocess-shared",
                            expected_sha256=digest, expected_size_bytes=len(payload),
                        )
                        if reference.sha256 != digest:
                            raise AssertionError("unexpected digest from publication")
                    outcomes.put(("ok", digest))
                except BaseException as exc:
                    outcomes.put(("error", type(exc).__name__ + ": " + str(exc)))

            workers = [context.Process(target=publish) for _ in range(4)]
            try:
                for worker in workers:
                    worker.start()
                for worker in workers:
                    worker.join(timeout=20)
                self.assertFalse(any(worker.is_alive() for worker in workers))
                self.assertEqual([worker.exitcode for worker in workers], [0] * 4)
                self.assertEqual(
                    [outcomes.get(timeout=5) for _ in workers],
                    [("ok", digest)] * 4,
                )
            finally:
                for worker in workers:
                    if worker.is_alive():
                        worker.terminate()
                    worker.join(timeout=2)
                outcomes.close()
                outcomes.join_thread()
            self.assertEqual(list(store.staging_root.iterdir()), [])
            self.assertEqual(
                sorted(path.name for path in store.metadata_root.iterdir()),
                ["multiprocess-shared.json"],
            )
            reference = store.put_bytes(
                payload, artifact_id="multiprocess-shared",
                expected_sha256=digest, expected_size_bytes=len(payload),
            )
            self.assertEqual(store.get_verified(reference), payload)

    def test_multiprocess_conflicting_artifact_ids_preserve_first_writer(self):
        if "fork" not in multiprocessing.get_all_start_methods():
            self.skipTest("multiprocess fork test requires POSIX fork")
        with tempfile.TemporaryDirectory() as tmp:
            store = VerifiedArtifactStore(Path(tmp) / "snapshots")
            payloads = (b"process candidate alpha", b"process candidate beta")
            context = multiprocessing.get_context("fork")
            start = context.Barrier(2)
            outcomes = context.Queue()

            def publish(payload):
                try:
                    start.wait(timeout=15)
                    reference = VerifiedArtifactStore(store.root).put_bytes(
                        payload, artifact_id="multiprocess-conflict",
                        expected_sha256=hashlib.sha256(payload).hexdigest(),
                        expected_size_bytes=len(payload),
                    )
                    outcomes.put(("winner", reference.sha256))
                except FileExistsError:
                    outcomes.put(("conflict", None))
                except BaseException as exc:
                    outcomes.put(("error", type(exc).__name__ + ": " + str(exc)))

            workers = [context.Process(target=publish, args=(payload,)) for payload in payloads]
            try:
                for worker in workers:
                    worker.start()
                for worker in workers:
                    worker.join(timeout=20)
                self.assertFalse(any(worker.is_alive() for worker in workers))
                self.assertEqual([worker.exitcode for worker in workers], [0, 0])
                results = [outcomes.get(timeout=5) for _ in workers]
            finally:
                for worker in workers:
                    if worker.is_alive():
                        worker.terminate()
                    worker.join(timeout=2)
                outcomes.close()
                outcomes.join_thread()
            winners = [value for status, value in results if status == "winner"]
            self.assertEqual(len(winners), 1, results)
            self.assertEqual(
                [status for status, _ in results].count("conflict"), 1, results
            )
            self.assertEqual(
                sorted(path.name for path in store.metadata_root.iterdir()),
                ["multiprocess-conflict.json"],
            )
            self.assertEqual(list(store.staging_root.iterdir()), [])
            winning_payload = next(
                payload for payload in payloads
                if hashlib.sha256(payload).hexdigest() == winners[0]
            )
            reference = store.put_bytes(
                winning_payload, artifact_id="multiprocess-conflict",
                expected_sha256=winners[0], expected_size_bytes=len(winning_payload),
            )
            self.assertEqual(store.get_verified(reference), winning_payload)

    def test_concurrent_identical_publication_is_consistent(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = VerifiedArtifactStore(Path(tmp) / "snapshots")
            payload = b"same immutable bytes from concurrent writers"
            digest = hashlib.sha256(payload).hexdigest()
            start = Barrier(8)

            def publish(_):
                start.wait(timeout=15)
                return store.put_bytes(
                    payload, artifact_id="concurrent-same",
                    expected_sha256=digest, expected_size_bytes=len(payload),
                )

            with ThreadPoolExecutor(max_workers=8) as pool:
                references = list(pool.map(publish, range(8)))
            self.assertTrue(all(ref == references[0] for ref in references))
            self.assertEqual(store.get_verified(references[0]), payload)
            self.assertEqual(list(store.staging_root.iterdir()), [])
            self.assertEqual(
                sorted(p.name for p in store.metadata_root.iterdir()),
                ["concurrent-same.json"],
            )

    def test_concurrent_conflicting_artifact_ids_do_not_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = VerifiedArtifactStore(Path(tmp) / "snapshots")
            payloads = [b"candidate one", b"candidate two"]
            start = Barrier(2)

            def publish(payload):
                start.wait(timeout=15)
                try:
                    return store.put_bytes(
                        payload, artifact_id="concurrent-conflict",
                        expected_sha256=hashlib.sha256(payload).hexdigest(),
                        expected_size_bytes=len(payload),
                    )
                except FileExistsError:
                    return None

            with ThreadPoolExecutor(max_workers=2) as pool:
                results = list(pool.map(publish, payloads))
            winners = [reference for reference in results if reference is not None]
            self.assertEqual(len(winners), 1)
            self.assertIn(store.get_verified(winners[0]), payloads)
            self.assertEqual(list(store.staging_root.iterdir()), [])
            self.assertEqual(
                sorted(p.name for p in store.metadata_root.iterdir()),
                ["concurrent-conflict.json"],
            )

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
