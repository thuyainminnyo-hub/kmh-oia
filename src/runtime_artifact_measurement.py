"""Measure pinned runtime artifact bytes with SHA-256.

Byte measurement binds a digest to the exact bytes read by this helper, but
does not authenticate the origin or signer of those bytes. Verify signed
provenance separately and load the measured byte payload, not a mutable path.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
from pathlib import Path


def normalize_sha256(value: str) -> str:
    """Normalize a SHA-256 digest or reject a malformed value."""
    if not isinstance(value, str):
        raise ValueError("SHA-256 digest must be a string")
    candidate = value.strip()
    if candidate.startswith("sha256:"):
        candidate = candidate[7:]
    if len(candidate) != 64 or any(ch not in "0123456789abcdefABCDEF" for ch in candidate):
        raise ValueError("SHA-256 digest must contain exactly 64 hexadecimal characters")
    return candidate.lower()


@dataclass(frozen=True)
class MeasuredArtifact:
    """Exact byte payload and content address measured together."""
    path: str
    sha256: str
    content: bytes


def measure_artifact(path: str | Path) -> MeasuredArtifact:
    """Read artifact bytes once and return their content address."""
    resolved = Path(path)
    content = resolved.read_bytes()
    return MeasuredArtifact(
        path=str(resolved),
        sha256=hashlib.sha256(content).hexdigest(),
        content=content,
    )


def require_artifact_digest(path: str | Path, expected_sha256: str) -> MeasuredArtifact:
    """Fail closed unless measured file bytes match the pinned digest."""
    expected = normalize_sha256(expected_sha256)
    artifact = measure_artifact(path)
    if artifact.sha256 != expected:
        raise ValueError(
            f"artifact SHA-256 mismatch for {artifact.path}: expected {expected}, got {artifact.sha256}"
        )
    return artifact


def require_bytes_digest(content: bytes, expected_sha256: str, *, artifact_name: str) -> str:
    """Validate a specific in-memory byte payload against a pinned digest."""
    if not isinstance(content, bytes):
        raise ValueError("artifact content must be bytes")
    if not isinstance(artifact_name, str) or not artifact_name.strip():
        raise ValueError("artifact_name is required")
    expected = normalize_sha256(expected_sha256)
    actual = hashlib.sha256(content).hexdigest()
    if actual != expected:
        raise ValueError(
            f"artifact SHA-256 mismatch for {artifact_name.strip()}: expected {expected}, got {actual}"
        )
    return actual
