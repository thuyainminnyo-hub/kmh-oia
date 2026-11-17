"""Durable local content-addressed storage for verified production artifacts.

The store admits only regular files contained by an explicitly allowed root.
It reads the source once, hashes the exact bytes while copying them to a
same-filesystem temporary file, fsyncs the file, and atomically publishes the
blob without replacing an existing digest. A separate immutable metadata
record preserves artifact identity independently from byte identity.

This is a local, single-host primitive. It is not encrypted, remotely
replicated, or protected against a privileged host administrator.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import stat
import tempfile
import uuid
from dataclasses import asdict, dataclass
from pathlib import Path


_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_ARTIFACT_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
_VERIFICATION_VERSION = "cas-v1"
_CHUNK_SIZE = 1024 * 1024


@dataclass(frozen=True)
class VerifiedSnapshot:
    """Immutable locator and integrity facts for one admitted artifact."""

    artifact_id: str
    sha256: str
    size_bytes: int
    storage_key: str
    verification_version: str = _VERIFICATION_VERSION

    def __post_init__(self) -> None:
        if not isinstance(self.artifact_id, str) or not _ARTIFACT_ID_RE.fullmatch(self.artifact_id):
            raise ValueError("artifact_id must be a non-empty safe identifier")
        if not isinstance(self.sha256, str) or not _SHA256_RE.fullmatch(self.sha256):
            raise ValueError("sha256 must be a lowercase SHA-256 digest")
        if isinstance(self.size_bytes, bool) or not isinstance(self.size_bytes, int) or self.size_bytes <= 0:
            raise ValueError("size_bytes must be a positive integer")
        expected_key = f"sha256/{self.sha256[:2]}/{self.sha256[2:4]}/{self.sha256}"
        if self.storage_key != expected_key:
            raise ValueError("storage_key does not match sha256")
        if self.verification_version != _VERIFICATION_VERSION:
            raise ValueError("unsupported snapshot verification version")


class VerifiedArtifactStore:
    """Store and verify immutable artifact snapshots on one local filesystem."""

    def __init__(self, root: str | Path) -> None:
        if not isinstance(root, (str, Path)) or not str(root).strip():
            raise ValueError("snapshot root must be a non-empty path")
        self.root = Path(root).expanduser().resolve()
        self.blob_root = self.root / "sha256"
        self.metadata_root = self.root / "artifacts"
        self.blob_root.mkdir(parents=True, exist_ok=True)
        self.metadata_root.mkdir(parents=True, exist_ok=True)
        self._fsync_directory_chain(self.metadata_root, self.root)
        if self.root.parent.exists():
            self._fsync_directory(self.root.parent)

    @staticmethod
    def _fsync_directory(path: Path) -> None:
        """Persist directory-entry changes where the platform supports it."""
        if os.name == "nt":
            return
        flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
        fd = os.open(path, flags)
        try:
            os.fsync(fd)
        finally:
            os.close(fd)

    @classmethod
    def _fsync_directory_chain(cls, path: Path, stop_at: Path) -> None:
        """Fsync a directory and each ancestor through stop_at, inclusive."""
        current = path
        stop = stop_at.resolve()
        if current.resolve() != stop and stop not in current.resolve().parents:
            raise ValueError("directory fsync boundary is not an ancestor")
        while True:
            cls._fsync_directory(current)
            if current.resolve() == stop:
                break
            current = current.parent

    def _blob_path(self, digest: str) -> Path:
        if not isinstance(digest, str) or not _SHA256_RE.fullmatch(digest):
            raise ValueError("invalid snapshot digest")
        return self.blob_root / digest[:2] / digest[2:4] / digest

    def _metadata_path(self, artifact_id: str) -> Path:
        if not isinstance(artifact_id, str) or not _ARTIFACT_ID_RE.fullmatch(artifact_id):
            raise ValueError("artifact_id must be a non-empty safe identifier")
        return self.metadata_root / f"{artifact_id}.json"

    @staticmethod
    def _reference_from_dict(data: dict) -> VerifiedSnapshot:
        try:
            return VerifiedSnapshot(
                artifact_id=data["artifact_id"],
                sha256=data["sha256"],
                size_bytes=data["size_bytes"],
                storage_key=data["storage_key"],
                verification_version=data["verification_version"],
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError("invalid snapshot metadata") from exc

    def put_verified(
        self,
        source_path: str | Path,
        *,
        allowed_root: str | Path,
        artifact_id: str | None = None,
    ) -> VerifiedSnapshot:
        """Ingest one contained regular file and atomically publish its snapshot."""
        if not isinstance(source_path, (str, Path)) or not str(source_path).strip():
            raise ValueError("source_path must be a non-empty path")
        allowed = Path(allowed_root).expanduser().resolve(strict=True)
        candidate = Path(source_path).expanduser()
        if not candidate.is_absolute():
            candidate = allowed / candidate
        try:
            resolved = candidate.resolve(strict=True)
            resolved.relative_to(allowed)
        except (FileNotFoundError, OSError, RuntimeError, ValueError) as exc:
            raise ValueError("source path is missing, unresolvable, or outside allowed_root") from exc

        if artifact_id is None:
            artifact_id = uuid.uuid4().hex
        metadata_path = self._metadata_path(artifact_id)
        if metadata_path.exists():
            raise FileExistsError(f"artifact_id already exists: {artifact_id}")

        # Resolve first, then refuse a symlink at the resolved final component.
        # The opened descriptor is checked again to ensure it is a regular file.
        nofollow = getattr(os, "O_NOFOLLOW", 0)
        flags = os.O_RDONLY | nofollow
        source_fd = os.open(resolved, flags)
        temp_path: Path | None = None
        try:
            source_stat = os.fstat(source_fd)
            if not stat.S_ISREG(source_stat.st_mode):
                raise ValueError("source must be a regular file")
            source_stream = os.fdopen(source_fd, "rb", closefd=False)

            # Stage on the destination filesystem so hard-link publication is atomic.
            staging_dir = self.root / ".staging"
            staging_dir.mkdir(parents=True, exist_ok=True)
            self._fsync_directory(self.root)
            temp_fd, temp_name = tempfile.mkstemp(prefix="snapshot-", dir=staging_dir)
            temp_path = Path(temp_name)
            digest = hashlib.sha256()
            size = 0
            try:
                with os.fdopen(temp_fd, "wb") as target:
                    while True:
                        chunk = source_stream.read(_CHUNK_SIZE)
                        if not chunk:
                            break
                        target.write(chunk)
                        digest.update(chunk)
                        size += len(chunk)
                    if size <= 0:
                        raise ValueError("artifact must not be empty")
                    source_after = os.fstat(source_fd)
                    stable_fields_before = (source_stat.st_dev, source_stat.st_ino, source_stat.st_size, source_stat.st_mtime_ns, source_stat.st_ctime_ns)
                    stable_fields_after = (source_after.st_dev, source_after.st_ino, source_after.st_size, source_after.st_mtime_ns, source_after.st_ctime_ns)
                    if stable_fields_before != stable_fields_after:
                        raise ValueError("source file changed during snapshot ingestion")
                    target.flush()
                    os.fsync(target.fileno())
            finally:
                source_stream.close()

            sha256 = digest.hexdigest()
            blob_path = self._blob_path(sha256)
            blob_path.parent.mkdir(parents=True, exist_ok=True)
            storage_key = blob_path.relative_to(self.root).as_posix()
            reference = VerifiedSnapshot(
                artifact_id=artifact_id,
                sha256=sha256,
                size_bytes=size,
                storage_key=storage_key,
            )

            try:
                # link() is atomic and fails if the immutable digest path exists.
                os.link(temp_path, blob_path)
                self._fsync_directory_chain(blob_path.parent, self.root)
            except FileExistsError:
                self._verify_blob(blob_path, sha256, size)
            except OSError as exc:
                raise RuntimeError("atomic snapshot publication failed; refusing non-atomic fallback") from exc

            metadata = json.dumps(asdict(reference), sort_keys=True, separators=(",", ":")) + "\n"
            self._publish_metadata(metadata_path, metadata)
            return reference
        finally:
            os.close(source_fd)
            if temp_path is not None:
                try:
                    temp_path.unlink(missing_ok=True)
                    if temp_path.parent.exists():
                        self._fsync_directory(temp_path.parent)
                except OSError:
                    # An orphan staging file is never trusted; recovery ignores it.
                    pass

    def _publish_metadata(self, path: Path, content: str) -> None:
        fd, name = tempfile.mkstemp(prefix="metadata-", dir=self.metadata_root)
        temp = Path(name)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as stream:
                stream.write(content)
                stream.flush()
                os.fsync(stream.fileno())
            # Metadata is unique by artifact_id; never overwrite a prior identity.
            os.link(temp, path)
            self._fsync_directory_chain(self.metadata_root, self.root)
        except FileExistsError:
            raise FileExistsError(f"artifact_id already exists: {path.stem}")
        finally:
            temp.unlink(missing_ok=True)

    @staticmethod
    def _read_regular_file(path: Path) -> bytes:
        """Read a regular file without following a final-component symlink."""
        try:
            if stat.S_ISLNK(path.lstat().st_mode):
                raise ValueError("refusing symlink in trusted snapshot storage")
            flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
            fd = os.open(path, flags)
        except FileNotFoundError:
            raise
        except OSError as exc:
            raise ValueError("unable to safely open trusted snapshot file") from exc
        try:
            info = os.fstat(fd)
            if not stat.S_ISREG(info.st_mode):
                raise ValueError("trusted snapshot entry is not a regular file")
            chunks = []
            with os.fdopen(fd, "rb", closefd=False) as stream:
                while True:
                    chunk = stream.read(_CHUNK_SIZE)
                    if not chunk:
                        break
                    chunks.append(chunk)
            return b"".join(chunks)
        finally:
            os.close(fd)

    @classmethod
    def _verify_blob(cls, path: Path, expected_digest: str, expected_size: int) -> None:
        try:
            payload = cls._read_regular_file(path)
        except FileNotFoundError as exc:
            raise ValueError("snapshot blob is missing") from exc
        if len(payload) != expected_size or hashlib.sha256(payload).hexdigest() != expected_digest:
            raise ValueError("existing snapshot blob failed integrity verification")

    def verify(self, reference: VerifiedSnapshot) -> VerifiedSnapshot:
        """Validate metadata and recompute the blob digest before trusting it."""
        if not isinstance(reference, VerifiedSnapshot):
            raise TypeError("reference must be a VerifiedSnapshot")
        metadata_path = self._metadata_path(reference.artifact_id)
        try:
            metadata_bytes = self._read_regular_file(metadata_path)
            stored = self._reference_from_dict(json.loads(metadata_bytes.decode("utf-8")))
        except FileNotFoundError as exc:
            raise ValueError("snapshot metadata is missing") from exc
        if stored != reference:
            raise ValueError("snapshot reference does not match stored metadata")
        blob_path = self._blob_path(reference.sha256)
        self._verify_blob(blob_path, reference.sha256, reference.size_bytes)
        return reference

    def get_verified(self, reference: VerifiedSnapshot) -> bytes:
        """Return bytes only after metadata, size, and digest have been verified."""
        self.verify(reference)
        blob_path = self._blob_path(reference.sha256)
        payload = self._read_regular_file(blob_path)
        if len(payload) != reference.size_bytes or hashlib.sha256(payload).hexdigest() != reference.sha256:
            raise ValueError("snapshot changed during retrieval")
        return payload

    def recover(self) -> tuple[VerifiedSnapshot, ...]:
        """Rebuild trusted references from metadata records; ignore orphan blobs."""
        recovered: list[VerifiedSnapshot] = []
        if not self.metadata_root.exists():
            return ()
        for metadata_path in sorted(self.metadata_root.glob("*.json")):
            try:
                metadata_bytes = self._read_regular_file(metadata_path)
                reference = self._reference_from_dict(json.loads(metadata_bytes.decode("utf-8")))
                if metadata_path.stem != reference.artifact_id:
                    continue
                self.verify(reference)
                recovered.append(reference)
            except (OSError, ValueError, TypeError, json.JSONDecodeError):
                # Corrupt or incomplete records remain on disk for investigation,
                # but are deliberately excluded from the trusted recovery set.
                continue
        return tuple(recovered)
