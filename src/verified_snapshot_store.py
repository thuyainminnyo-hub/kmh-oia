"""Descriptor-anchored, bounded content-addressed snapshot storage."""
from __future__ import annotations

import hashlib
import json
import os
import re
import secrets
import stat
from dataclasses import asdict, dataclass
from pathlib import Path

_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_ARTIFACT_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
_VERIFICATION_VERSION = "verified-bytes-v1"
_MAX_METADATA_BYTES = 16 * 1024
_MAX_SNAPSHOT_BYTES = 32 * 1024 * 1024


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
        if self.storage_key != f"sha256/{self.sha256[:2]}/{self.sha256[2:4]}/{self.sha256}":
            raise ValueError("storage_key does not match sha256")
        if self.verification_version != _VERIFICATION_VERSION:
            raise ValueError("unsupported snapshot verification version")


class VerifiedArtifactStore:
    """Store verified bytes using pinned directory FDs and no-overwrite links."""

    def __init__(self, root: str | Path) -> None:
        if not isinstance(root, (str, Path)) or not str(root).strip():
            raise ValueError("snapshot root must be a non-empty path")
        self.root = Path(root).expanduser().absolute()
        self._require_secure_primitives()
        self.root.mkdir(parents=True, exist_ok=True, mode=0o700)
        info = os.lstat(self.root)
        if not stat.S_ISDIR(info.st_mode) or stat.S_ISLNK(info.st_mode):
            raise RuntimeError("snapshot root must be a real directory, not a symlink")
        if info.st_uid != os.geteuid() or stat.S_IMODE(info.st_mode) & 0o077:
            raise RuntimeError("snapshot root must be owned by the service UID and private (mode 0700)")
        self._root_fd = os.open(self.root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC)
        self._verify_directory_fd(self._root_fd, "snapshot root")
        self.blob_root = self.root / "sha256"
        self.metadata_root = self.root / "artifacts"
        self.staging_root = self.root / ".staging"  # compatibility only; never used for publication
        for name in ("sha256", "artifacts"):
            fd = self._open_directory((name,), create=True)
            os.close(fd)

    @staticmethod
    def _require_secure_primitives() -> None:
        if os.name != "posix" or any(not hasattr(os, flag) for flag in ("O_NOFOLLOW", "O_DIRECTORY", "O_CLOEXEC")):
            raise RuntimeError("secure snapshot publication is unsupported on this platform")
        supported = getattr(os, "supports_dir_fd", set())
        if any(op not in supported for op in (os.open, os.link, os.unlink, os.stat)):
            raise RuntimeError("required descriptor-relative filesystem operations are unavailable")

    @staticmethod
    def _verify_directory_fd(fd: int, label: str) -> None:
        info = os.fstat(fd)
        if not stat.S_ISDIR(info.st_mode):
            raise RuntimeError(f"{label} is not a directory")
        if info.st_uid != os.geteuid() or stat.S_IMODE(info.st_mode) & 0o077:
            raise RuntimeError(f"{label} must be service-owned and private (mode 0700)")

    def close(self) -> None:
        fd = getattr(self, "_root_fd", -1)
        if fd >= 0:
            os.close(fd)
            self._root_fd = -1

    def __enter__(self) -> "VerifiedArtifactStore":
        if self._root_fd < 0:
            raise RuntimeError("snapshot store is closed")
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def _open_directory(self, parts: tuple[str, ...], *, create: bool = False) -> int:
        if self._root_fd < 0:
            raise RuntimeError("snapshot store is closed")
        current = os.dup(self._root_fd)
        try:
            for part in parts:
                if part in {"", ".", ".."} or "/" in part:
                    raise ValueError("unsafe snapshot directory component")
                if create:
                    try:
                        os.mkdir(part, 0o700, dir_fd=current)
                    except FileExistsError:
                        pass
                nxt = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC, dir_fd=current)
                self._verify_directory_fd(nxt, f"store directory {part}")
                os.close(current)
                current = nxt
            return current
        except Exception:
            os.close(current)
            raise

    @staticmethod
    def _write_all(fd: int, payload: bytes) -> None:
        view = memoryview(payload)
        while view:
            count = os.write(fd, view)
            if count <= 0:
                raise OSError("short write while publishing snapshot")
            view = view[count:]

    @staticmethod
    def _read_fd(fd: int, *, max_bytes: int, expected_size: int | None = None) -> bytes:
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
            block = os.read(fd, min(1024 * 1024, max_bytes - total + 1))
            if not block:
                break
            total += len(block)
            if total > max_bytes:
                raise ValueError("snapshot file exceeds size limit")
            chunks.append(block)
        after = os.fstat(fd)
        before_id = (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns, before.st_ctime_ns)
        after_id = (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns, after.st_ctime_ns)
        if before_id != after_id:
            raise ValueError("snapshot file changed while being read")
        if expected_size is not None and total != expected_size:
            raise ValueError("snapshot size mismatch")
        return b"".join(chunks)

    def _read_file(self, dirs: tuple[str, ...], name: str, *, max_bytes: int, expected_size: int | None = None) -> bytes:
        parent = self._open_directory(dirs)
        fd = -1
        try:
            fd = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC, dir_fd=parent)
            return self._read_fd(fd, max_bytes=max_bytes, expected_size=expected_size)
        except OSError as exc:
            raise ValueError("unable to safely open snapshot path; symlink or missing component") from exc
        finally:
            if fd >= 0:
                os.close(fd)
            os.close(parent)

    def _publish_file(self, dirs: tuple[str, ...], name: str, payload: bytes, *, max_bytes: int, expected_digest: str | None = None) -> bool:
        """Create an immutable name atomically; never replace an existing entry."""
        if len(payload) > max_bytes:
            raise ValueError("snapshot file exceeds size limit")
        parent = self._open_directory(dirs, create=True)
        temp = f".{name}.tmp-{secrets.token_hex(16)}"
        fd = -1
        temp_created = False
        try:
            fd = os.open(temp, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC, 0o600, dir_fd=parent)
            temp_created = True
            self._write_all(fd, payload)
            os.fsync(fd)
            os.fchmod(fd, 0o444)
            temp_info = os.fstat(fd)
            if not stat.S_ISREG(temp_info.st_mode) or temp_info.st_size != len(payload):
                raise ValueError("temporary snapshot identity or size verification failed")
            try:
                os.link(temp, name, src_dir_fd=parent, dst_dir_fd=parent, follow_symlinks=False)
                created = True
            except FileExistsError:
                created = False
            final_info = os.stat(name, dir_fd=parent, follow_symlinks=False)
            if not stat.S_ISREG(final_info.st_mode):
                raise ValueError("published snapshot is not a regular file")
            if created and (final_info.st_dev, final_info.st_ino) != (temp_info.st_dev, temp_info.st_ino):
                raise ValueError("published snapshot identity does not match temporary file")
            verify_fd = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC, dir_fd=parent)
            try:
                actual = self._read_fd(verify_fd, max_bytes=max_bytes, expected_size=len(payload))
            finally:
                os.close(verify_fd)
            if actual != payload:
                raise ValueError("existing snapshot failed byte-for-byte verification")
            if expected_digest is not None and hashlib.sha256(actual).hexdigest() != expected_digest:
                raise ValueError("published snapshot digest verification failed")
            os.unlink(temp, dir_fd=parent)
            temp_created = False
            os.fsync(parent)
            return created
        finally:
            if fd >= 0:
                os.close(fd)
            # Never unlink a colliding name that this call did not create.
            if temp_created:
                try:
                    os.unlink(temp, dir_fd=parent)
                except FileNotFoundError:
                    pass
            os.close(parent)

    @staticmethod
    def _blob_location(digest: str) -> tuple[tuple[str, ...], str]:
        if not _SHA256_RE.fullmatch(digest):
            raise ValueError("invalid snapshot digest")
        return ("sha256", digest[:2], digest[2:4]), digest

    def put_bytes(self, payload: bytes, *, artifact_id: str, expected_sha256: str, expected_size_bytes: int) -> VerifiedSnapshot:
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
        reference = VerifiedSnapshot(artifact_id, digest, len(payload), f"sha256/{digest[:2]}/{digest[2:4]}/{digest}")
        blob_dirs, blob_name = self._blob_location(digest)
        self._publish_file(blob_dirs, blob_name, payload, max_bytes=_MAX_SNAPSHOT_BYTES, expected_digest=digest)
        metadata = (json.dumps(asdict(reference), sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
        self._publish_file(("artifacts",), f"{artifact_id}.json", metadata, max_bytes=_MAX_METADATA_BYTES)
        return reference

    def get_verified(self, reference: VerifiedSnapshot) -> bytes:
        if not isinstance(reference, VerifiedSnapshot):
            raise TypeError("reference must be a VerifiedSnapshot")
        metadata = self._read_file(("artifacts",), f"{reference.artifact_id}.json", max_bytes=_MAX_METADATA_BYTES)
        try:
            recorded = json.loads(metadata.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ValueError("snapshot metadata is invalid") from exc
        if recorded != asdict(reference):
            raise ValueError("snapshot reference does not match stored metadata")
        dirs, name = self._blob_location(reference.sha256)
        payload = self._read_file(dirs, name, max_bytes=_MAX_SNAPSHOT_BYTES, expected_size=reference.size_bytes)
        if hashlib.sha256(payload).hexdigest() != reference.sha256:
            raise ValueError("snapshot blob failed digest/size verification")
        return payload
