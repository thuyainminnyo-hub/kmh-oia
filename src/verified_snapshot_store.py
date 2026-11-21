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
import secrets
import stat
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path

_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_ARTIFACT_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
_VERIFICATION_VERSION = "verified-bytes-v1"
_MAX_METADATA_BYTES = 16 * 1024
_MAX_SNAPSHOT_BYTES = 32 * 1024 * 1024  # Match src.image_integrity._MAX_FILE_BYTES.


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
        if self.size_bytes > _MAX_SNAPSHOT_BYTES:
            raise ValueError("snapshot size exceeds policy limit")
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

    def _read_no_follow(
        self,
        path: Path,
        *,
        expected_size: int | None = None,
        max_bytes: int,
    ) -> bytes:
        """Read a regular store file with bounded, descriptor-relative no-follow access.

        The root directory is opened component-by-component from the filesystem
        root. Every descendant is then opened relative to a trusted directory
        descriptor, so symlinks in intermediate components are rejected too.
        """
        if isinstance(max_bytes, bool) or not isinstance(max_bytes, int) or max_bytes <= 0:
            raise ValueError("max_bytes must be a positive integer")
        if expected_size is not None:
            if isinstance(expected_size, bool) or not isinstance(expected_size, int) or expected_size <= 0:
                raise ValueError("expected_size must be a positive integer")
            if expected_size > max_bytes:
                raise ValueError("expected snapshot size exceeds read limit")

        relative = path.relative_to(self.root)
        if not relative.parts or any(part in {"", ".", ".."} for part in relative.parts):
            raise ValueError("snapshot path must be a safe relative file path")

        nofollow = getattr(os, "O_NOFOLLOW", 0)
        directory = getattr(os, "O_DIRECTORY", 0)
        nonblock = getattr(os, "O_NONBLOCK", 0)
        if (
            not nofollow
            or not directory
            or os.open not in getattr(os, "supports_dir_fd", set())
        ):
            raise RuntimeError("secure snapshot reads are unsupported on this platform")

        root_fd = -1
        parent_fds: list[int] = []
        fd = -1
        try:
            # Resolve the trusted root without following any path component.
            root_fd = os.open(os.sep, os.O_RDONLY | directory | nofollow)
            for component in self.root.parts[1:]:
                next_fd = os.open(
                    component, os.O_RDONLY | directory | nofollow, dir_fd=root_fd
                )
                os.close(root_fd)
                root_fd = next_fd

            parent_fd = root_fd
            for component in relative.parts[:-1]:
                parent_fd = os.open(
                    component, os.O_RDONLY | directory | nofollow, dir_fd=parent_fd
                )
                parent_fds.append(parent_fd)

            fd = os.open(
                relative.parts[-1], os.O_RDONLY | nofollow | nonblock, dir_fd=parent_fd
            )
            before = os.fstat(fd)
            if not stat.S_ISREG(before.st_mode):
                raise ValueError("snapshot entry is not a regular file")
            if before.st_size < 0 or before.st_size > max_bytes:
                raise ValueError("snapshot file exceeds size limit")
            if expected_size is not None and before.st_size != expected_size:
                raise ValueError("snapshot size mismatch")

            chunks: list[bytes] = []
            total = 0
            while True:
                # Read at most one byte beyond the policy ceiling to detect growth.
                request_size = min(1024 * 1024, max_bytes - total + 1)
                block = os.read(fd, request_size)
                if not block:
                    break
                total += len(block)
                if total > max_bytes:
                    raise ValueError("snapshot file exceeds size limit")
                chunks.append(block)

            after = os.fstat(fd)
            identity_before = (
                before.st_dev, before.st_ino, before.st_size,
                before.st_mtime_ns, before.st_ctime_ns,
            )
            identity_after = (
                after.st_dev, after.st_ino, after.st_size,
                after.st_mtime_ns, after.st_ctime_ns,
            )
            if identity_before != identity_after:
                raise ValueError("snapshot file changed while being read")
            if expected_size is not None and total != expected_size:
                raise ValueError("snapshot size mismatch")
            return b"".join(chunks)
        except OSError as exc:
            raise ValueError(
                "unable to safely open snapshot path; symlink or missing component"
            ) from exc
        finally:
            if fd >= 0:
                os.close(fd)
            for parent_fd in reversed(parent_fds):
                os.close(parent_fd)
            if root_fd >= 0:
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
        if len(payload) > _MAX_SNAPSHOT_BYTES or expected_size_bytes > _MAX_SNAPSHOT_BYTES:
            raise ValueError("snapshot size exceeds policy limit")
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
        metadata_path = self._metadata_path(artifact_id)

        # Reject a substituted staging-directory symlink before publishing.
        # Keep the verified staging descriptor open through creation and cleanup.
        nofollow = getattr(os, "O_NOFOLLOW", 0)
        directory = getattr(os, "O_DIRECTORY", 0)
        if not nofollow or not directory:
            raise RuntimeError("secure staging directory checks are unsupported")
        if not {os.open, os.link, os.unlink, os.mkdir}.issubset(os.supports_dir_fd):
            raise RuntimeError("descriptor-relative snapshot publication is unsupported")
        # Resolve each blob component relative to a verified parent descriptor.
        # Reject symlinks even when an attacker substitutes a directory.
        root_fd = os.open(self.root, os.O_RDONLY | directory | nofollow)
        blob_fds = []
        try:
            parent_fd = root_fd
            for component in ("sha256", digest[:2], digest[2:4]):
                try:
                    os.mkdir(component, mode=0o700, dir_fd=parent_fd)
                except FileExistsError:
                    pass
                child_fd = os.open(
                    component, os.O_RDONLY | directory | nofollow, dir_fd=parent_fd,
                )
                blob_fds.append(child_fd)
                parent_fd = child_fd
        except BaseException:
            for opened_fd in reversed(blob_fds):
                os.close(opened_fd)
            os.close(root_fd)
            raise
        blob_parent_fd = blob_fds[-1]
        try:
            staging_fd = os.open(self.staging_root, os.O_RDONLY | directory | nofollow)
        except BaseException:
            for opened_fd in reversed(blob_fds):
                os.close(opened_fd)
            os.close(root_fd)
            raise
        temp_name = "snapshot-" + secrets.token_hex(16)
        try:
            fd = os.open(
                temp_name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | nofollow,
                0o600, dir_fd=staging_fd,
            )
            try:
                with os.fdopen(fd, "wb") as stream:
                    stream.write(payload)
                    stream.flush()
                    os.fsync(stream.fileno())
                    os.fchmod(stream.fileno(), 0o444)
                try:
                    os.link(
                        temp_name, digest, src_dir_fd=staging_fd,
                        dst_dir_fd=blob_parent_fd, follow_symlinks=False,
                    )
                    os.fsync(blob_parent_fd)
                except FileExistsError:
                    existing = self._read_no_follow(
                        blob_path, expected_size=len(payload), max_bytes=_MAX_SNAPSHOT_BYTES
                    )
                    if len(existing) != len(payload) or hashlib.sha256(existing).hexdigest() != digest:
                        raise ValueError("existing content-addressed snapshot failed integrity verification")

                encoded = (json.dumps(asdict(reference), sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
                metadata_fd = os.open(self.metadata_root, os.O_RDONLY | directory | nofollow)
                try:
                    metadata_name = "metadata-" + secrets.token_hex(16)
                    meta_fd = os.open(
                        metadata_name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | nofollow,
                        0o600, dir_fd=metadata_fd,
                    )
                    try:
                        with os.fdopen(meta_fd, "wb") as stream:
                            stream.write(encoded)
                            stream.flush()
                            os.fsync(stream.fileno())
                            os.fchmod(stream.fileno(), 0o444)
                        try:
                            os.link(
                                metadata_name, f"{artifact_id}.json",
                                src_dir_fd=metadata_fd, dst_dir_fd=metadata_fd,
                                follow_symlinks=False,
                            )
                            os.fsync(metadata_fd)
                        except FileExistsError:
                            previous = self._read_no_follow(metadata_path, max_bytes=_MAX_METADATA_BYTES)
                            if previous != encoded:
                                raise FileExistsError(f"artifact_id already exists with different snapshot: {artifact_id}")
                    finally:
                        os.unlink(metadata_name, dir_fd=metadata_fd)
                finally:
                    os.close(metadata_fd)
                return reference
            finally:
                os.unlink(temp_name, dir_fd=staging_fd)
        finally:
            os.close(staging_fd)
            for opened_fd in reversed(blob_fds):
                os.close(opened_fd)
            os.close(root_fd)

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
        payload = self._read_no_follow(
            self._blob_path(reference.sha256),
            expected_size=reference.size_bytes,
            max_bytes=_MAX_SNAPSHOT_BYTES,
        )
        if len(payload) != reference.size_bytes or hashlib.sha256(payload).hexdigest() != reference.sha256:
            raise ValueError("snapshot blob failed digest/size verification")
        return payload
