import hashlib
import os
import stat
import subprocess
import sys
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch

from src.verified_snapshot_store import VerifiedArtifactStore, VerifiedSnapshot


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
                # Same length forces the no-overwrite path to compare bytes,
                # rather than rejecting the collision on size alone.
                store._publish_file(("artifacts",), "item.json", b"originaL", max_bytes=100)
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



    def test_pub_11_mode_change_is_synced_before_publication(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = VerifiedArtifactStore(Path(tmp) / "store")
            real_fchmod = os.fchmod
            real_fsync = os.fsync
            events = []

            def record_fchmod(fd, mode):
                events.append(("fchmod", mode))
                return real_fchmod(fd, mode)

            def record_fsync(fd):
                events.append(("fsync", os.fstat(fd).st_mode))
                return real_fsync(fd)

            with patch("src.verified_snapshot_store.os.fchmod", side_effect=record_fchmod), \
                 patch("src.verified_snapshot_store.os.fsync", side_effect=record_fsync):
                store._publish_file(("artifacts",), "durable.json", b"durable",
                                    max_bytes=100)

            fchmod_index = next(i for i, event in enumerate(events) if event[0] == "fchmod")
            file_fsync_index = next(
                i for i, event in enumerate(events)
                if event[0] == "fsync" and stat.S_ISREG(event[1])
            )
            self.assertLess(fchmod_index, file_fsync_index)

    def test_pub_12_new_nested_directory_syncs_its_parent(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = VerifiedArtifactStore(Path(tmp) / "store")
            real_mkdir = os.mkdir
            real_fsync = os.fsync
            events = []

            def record_mkdir(path, mode=0o777, *, dir_fd=None):
                result = real_mkdir(path, mode, dir_fd=dir_fd)
                events.append(("mkdir", path))
                return result

            def record_fsync(fd):
                result = real_fsync(fd)
                events.append(("fsync", os.fstat(fd).st_ino))
                return result

            with patch("src.verified_snapshot_store.os.mkdir", side_effect=record_mkdir), \
                 patch("src.verified_snapshot_store.os.fsync", side_effect=record_fsync):
                nested_fd = store._open_directory(("sha256", "ab", "cd"), create=True)
                os.close(nested_fd)

            self.assertGreaterEqual(len(events), 4)
            self.assertEqual([event[0] for event in events[:4]], ["mkdir", "fsync", "mkdir", "fsync"])

    def test_pub_13_root_path_rejects_symlinked_ancestor(self):
        if not hasattr(os, "symlink"):
            self.skipTest("symlinks unavailable")
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            real_parent = base / "real-parent"
            real_parent.mkdir(mode=0o700)
            symlink_parent = base / "linked-parent"
            try:
                symlink_parent.symlink_to(real_parent, target_is_directory=True)
            except (OSError, NotImplementedError):
                self.skipTest("symlink creation unavailable")
            unsafe_root = symlink_parent / "store"
            with self.assertRaises((OSError, RuntimeError)):
                VerifiedArtifactStore(unsafe_root)


    def test_pub_14_compatibility_reader_rejects_invalid_bounds(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = VerifiedArtifactStore(Path(tmp) / "store")
            target = store.metadata_root / "read.json"
            self.assertTrue(store._publish_file(("artifacts",), "read.json",
                                                b"bounded", max_bytes=100))
            with self.assertRaisesRegex(ValueError, "max_bytes"):
                store._read_no_follow(target, max_bytes=True)
            with self.assertRaisesRegex(ValueError, "expected_size"):
                store._read_no_follow(target, expected_size=True, max_bytes=100)
            with self.assertRaisesRegex(ValueError, "expected_size"):
                store._read_no_follow(target, expected_size=0, max_bytes=100)
            with self.assertRaisesRegex(ValueError, "read limit"):
                store._read_no_follow(target, expected_size=101, max_bytes=100)


    def test_pub_07_different_uid_process_cannot_write_store(self):
        if os.name != "posix":
            self.skipTest("different-UID isolation requires POSIX")
        import pwd
        import shutil

        sudo = shutil.which("sudo")
        if sudo is None:
            self.skipTest("sudo is unavailable; run the dedicated UID isolation check on the Linux target")
        try:
            attacker = pwd.getpwnam("nobody")
        except KeyError:
            self.skipTest("unprivileged nobody account is unavailable")
        if attacker.pw_uid == os.geteuid():
            self.skipTest("service process already runs as the nobody UID")

        with tempfile.TemporaryDirectory() as tmp:
            store = VerifiedArtifactStore(Path(tmp) / "store")
            target = store.root / "attacker-created"
            probe = (
                "import os,sys\n"
                "path=sys.argv[1]\n"
                "try:\n"
                " fd=os.open(path, os.O_WRONLY|os.O_CREAT|os.O_EXCL, 0o600)\n"
                "except PermissionError:\n"
                " sys.exit(0)\n"
                "except OSError:\n"
                " sys.exit(3)\n"
                "else:\n"
                " os.close(fd)\n"
                " os.unlink(path)\n"
                " sys.exit(2)\n"
            )
            result = subprocess.run(
                [sudo, "-n", "-u", "nobody", "--", sys.executable, "-c", probe, str(target)],
                cwd="/",
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
            self.assertFalse(target.exists())

    def _run_writer_until_hardlink_exit(self, root: Path, artifact_id: str, payload: bytes,
                                        stop_after_link: int) -> int:
        if not hasattr(os, "fork"):
            self.skipTest("process-level crash injection requires os.fork")
        digest = hashlib.sha256(payload).hexdigest()
        pid = os.fork()
        if pid == 0:
            try:
                child_store = VerifiedArtifactStore(root)
                real_link = os.link
                link_count = 0

                def exit_after_link(src, dst, **kwargs):
                    nonlocal link_count
                    result = real_link(src, dst, **kwargs)
                    link_count += 1
                    if link_count == stop_after_link:
                        # Abrupt process termination: no Python finally blocks run.
                        os._exit(73)
                    return result

                os.link = exit_after_link
                child_store.put_bytes(
                    payload,
                    artifact_id=artifact_id,
                    expected_sha256=digest,
                    expected_size_bytes=len(payload),
                )
                os._exit(0)
            except BaseException:
                os._exit(74)
        _, status = os.waitpid(pid, 0)
        return os.waitstatus_to_exitcode(status)

    def test_pub_15_process_exit_after_blob_link_leaves_no_committed_metadata(self):
        if os.name != "posix":
            self.skipTest("process-level crash injection requires POSIX")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "store"
            parent_store = VerifiedArtifactStore(root)
            payload = b"process stopped after blob publication"
            digest = hashlib.sha256(payload).hexdigest()
            artifact_id = "process-crash-blob"
            exit_code = self._run_writer_until_hardlink_exit(root, artifact_id, payload, 1)
            self.assertEqual(exit_code, 73)

            reference = VerifiedSnapshot(
                artifact_id=artifact_id,
                sha256=digest,
                size_bytes=len(payload),
                storage_key=f"sha256/{digest[:2]}/{digest[2:4]}/{digest}",
            )
            self.assertTrue((root / reference.storage_key).is_file())
            self.assertFalse((parent_store.metadata_root / f"{artifact_id}.json").exists())
            with self.assertRaises(ValueError):
                parent_store.get_verified(reference)

    def test_pub_16_process_exit_after_metadata_link_keeps_logically_committed_pair(self):
        if os.name != "posix":
            self.skipTest("process-level crash injection requires POSIX")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "store"
            parent_store = VerifiedArtifactStore(root)
            payload = b"process stopped after metadata publication"
            digest = hashlib.sha256(payload).hexdigest()
            artifact_id = "process-crash-metadata"
            exit_code = self._run_writer_until_hardlink_exit(root, artifact_id, payload, 2)
            self.assertEqual(exit_code, 73)

            reference = VerifiedSnapshot(
                artifact_id=artifact_id,
                sha256=digest,
                size_bytes=len(payload),
                storage_key=f"sha256/{digest[:2]}/{digest[2:4]}/{digest}",
            )
            metadata = parent_store.metadata_root / f"{artifact_id}.json"
            self.assertTrue(metadata.is_file())
            self.assertEqual(parent_store.get_verified(reference), payload)


if __name__ == "__main__":
    unittest.main()
