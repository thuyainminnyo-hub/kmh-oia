"""Content-addressed snapshots for bytes already verified by an upstream gate.

This module accepts immutable in-memory payloads only. It never reopens the
mutable source artifact. Blobs are published by atomic hard-link creation and
are verified again whenever they are retrieved.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import stat
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path

_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_ARTIFACT_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
_VERIFICATION_VERSION = "verified-bytes-v1"
_MAX_METADATA_BYTES = 16 * 1024


@dataclass(frozen=True)
class VerifiedSnapshot:
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
        expected = f"sha256/{self.sha256[:2]}/{self.sha256[2:4]}/{self.sha256}"
        if self.storage_key != expected:
            raise ValueError("storage_key does not match sha256")
        if self.verification_version != _VERIFICATION_VERSION:
            raise ValueError("unsupported snapshot verification version")


class VerifiedArtifactStore:
    """Publish and retrieve immutable, content-addressed byte snapshots."""

    def __init__(self, root: str | Path) -> None:
        if not isinstance(root, (str, Path)) or not str(root).strip():
            raise ValueError("snapshot root must be a non-empty path")
        self.root = Path(root).expanduser().resolve()
        self.blob_root = self.root / "sha256"
        self.metadata_root = self.root / "artifacts"
        self.staging_root = self.root / ".staging"
        for directory in (self.blob_root, self.metadata_root, self.staging_root):
            directory.mkdir(parents=True, exist_ok=True)

    def _blob_path(self, digest: str) -> Path:
        if not _SHA256_RE.fullmatch(digest):
            raise ValueError("invalid snapshot digest")
        return self.blob_root / digest[:2] / digest[2:4] / digest

    def _metadata_path(self, artifact_id: str) -> Path:
        if not _ARTIFACT_ID_RE.fullmatch(artifact_id):
            raise ValueError("artifact_id must be a non-empty safe identifier")
        return self.metadata_root / f"{artifact_id}.json"

    def _fsync_dir(self, path: Path) -> None:
        if os.name == "nt":
            return
        fd = os.open(path, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
        try:
            os.fsync(fd)
        finally:
            os.close(fd)

    def _read_no_follow(self, path: Path, *, max_bytes: int | None = None) -> bytes:
        """Read a regular store file via descriptor-relative O_NOFOLLOW opens."""
        relative = path.relative_to(self.root)
        if not relative.parts:
            raise ValueError("snapshot path must identify a file")
        nofollow = getattr(os, "O_NOFOLLOW", 0)
        directory = getattr(os, "O_DIRECTORY", 0)
        if not nofollow or not directory or os.open not in getattr(os, "supports_dir_fd", set()):
            raise RuntimeError("secure snapshot reads are unsupported on this platform")
        root_fd = os.open(self.root, os.O_RDONLY | directory | nofollow)
        parent_fds: list[int] = []
        fd = -1
        try:
            parent_fd = root_fd
            for component in relative.parts[:-1]:
                parent_fd = os.open(component, os.O_RDONLY | directory | nofollow, dir_fd=parent_fd)
                parent_fds.append(parent_fd)
            fd = os.open(relative.parts[-1], os.O_RDONLY | nofollow, dir_fd=parent_fd)
            info = os.fstat(fd)
            if not stat.S_ISREG(info.st_mode):
                raise ValueError("snapshot entry is not a regular file")
            chunks: list[bytes] = []
            total = 0
            while True:
                block = os.read(fd, 1024 * 1024 if max_bytes is None else min(1024 * 1024, max_bytes - total + 1))
                if not block:
                    break
                total += len(block)
                if max_bytes is not None and total > max_bytes:
                    raise ValueError("snapshot metadata exceeds size limit")
                chunks.append(block)
            return b"".join(chunks)
        except OSError as exc:
            raise ValueError("unable to safely open snapshot path; symlink or missing component") from exc
        finally:
            if fd >= 0:
                os.close(fd)
            for parent_fd in reversed(parent_fds):
                os.close(parent_fd)
            os.close(root_fd)

    def put_bytes(
        self,
        payload: bytes,
        *,
        artifact_id: str,
        expected_sha256: str,
        expected_size_bytes: int,
    ) -> VerifiedSnapshot:
        """Atomically store bytes only when they match the upstream verified facts."""
        if not isinstance(payload, bytes) or not payload:
            raise ValueError("verified payload must be non-empty bytes")
        if not isinstance(expected_sha256, str) or not _SHA256_RE.fullmatch(expected_sha256):
            raise ValueError("expected_sha256 must be a lowercase SHA-256 digest")
        if isinstance(expected_size_bytes, bool) or not isinstance(expected_size_bytes, int) or expected_size_bytes <= 0:
            raise ValueError("expected_size_bytes must be a positive integer")
        digest = hashlib.sha256(payload).hexdigest()
        if len(payload) != expected_size_bytes or digest != expected_sha256:
            raise ValueError("verified payload does not match PNG integrity digest/size")
        reference = VerifiedSnapshot(
            artifact_id=artifact_id,
            sha256=digest,
            size_bytes=len(payload),
            storage_key=f"sha256/{digest[:2]}/{digest[2:4]}/{digest}",
        )
        blob_path = self._blob_path(digest)
        blob_path.parent.mkdir(parents=True, exist_ok=True)
        metadata_path = self._metadata_path(artifact_id)

        fd, temp_name = tempfile.mkstemp(prefix="snapshot-", dir=self.staging_root)
        temp_path = Path(temp_name)
        try:
            with os.fdopen(fd, "wb") as stream:
                stream.write(payload)
                stream.flush()
                os.fsync(stream.fileno())
                os.fchmod(stream.fileno(), 0o444)
            try:
                os.link(temp_path, blob_path)
                self._fsync_dir(blob_path.parent)
            except FileExistsError:
                existing = self._read_no_follow(blob_path)
                if len(existing) != len(payload) or hashlib.sha256(existing).hexdigest() != digest:
                    raise ValueError("existing content-addressed snapshot failed integrity verification")

            encoded = (json.dumps(asdict(reference), sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
            meta_fd, meta_name = tempfile.mkstemp(prefix="metadata-", dir=self.metadata_root)
            meta_temp = Path(meta_name)
            try:
                with os.fdopen(meta_fd, "wb") as stream:
                    stream.write(encoded)
                    stream.flush()
                    os.fsync(stream.fileno())
                    os.fchmod(stream.fileno(), 0o444)
                try:
                    os.link(meta_temp, metadata_path)
                    self._fsync_dir(self.metadata_root)
                except FileExistsError:
                    previous = self._read_no_follow(metadata_path, max_bytes=_MAX_METADATA_BYTES)
                    if previous != encoded:
                        raise FileExistsError(f"artifact_id already exists with different snapshot: {artifact_id}")
            finally:
                meta_temp.unlink(missing_ok=True)
            return reference
        finally:
            temp_path.unlink(missing_ok=True)

    def get_verified(self, reference: VerifiedSnapshot) -> bytes:
        if not isinstance(reference, VerifiedSnapshot):
            raise TypeError("reference must be a VerifiedSnapshot")
        metadata = self._read_no_follow(
            self._metadata_path(reference.artifact_id), max_bytes=_MAX_METADATA_BYTES
        )
        try:
            recorded = json.loads(metadata.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ValueError("snapshot metadata is invalid") from exc
        if recorded != asdict(reference):
            raise ValueError("snapshot reference does not match stored metadata")
        payload = self._read_no_follow(self._blob_path(reference.sha256))
        if len(payload) != reference.size_bytes or hashlib.sha256(payload).hexdigest() != reference.sha256:
            raise ValueError("snapshot blob failed digest/size verification")
        return payload
