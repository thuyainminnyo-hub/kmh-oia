"""Verify that an execution result points to a real local output file.

This gate proves only basic filesystem facts (contained path, regular file,
non-empty bytes). It does not judge content quality or safety.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class OutputVerification:
    verified: bool
    resolved_path: str | None = None
    size_bytes: int = 0
    reason: str | None = None


def verify_output_file(output_path: str, allowed_root: str | Path) -> OutputVerification:
    """Check output existence, non-zero size, and containment under allowed_root."""
    if not isinstance(output_path, str) or not output_path.strip():
        return OutputVerification(False, reason="output_path must be a non-empty string")
    root = Path(allowed_root).resolve()
    candidate = Path(output_path)
    if not candidate.is_absolute():
        candidate = root / candidate
    try:
        resolved = candidate.resolve(strict=True)
    except (FileNotFoundError, OSError, RuntimeError):
        return OutputVerification(False, reason="output file does not exist or cannot be resolved")
    try:
        resolved.relative_to(root)
    except ValueError:
        return OutputVerification(False, reason="output path escapes the allowed root")
    if not resolved.is_file():
        return OutputVerification(False, reason="output path is not a regular file")
    try:
        size = resolved.stat().st_size
    except OSError:
        return OutputVerification(False, reason="output file cannot be inspected")
    if size <= 0:
        return OutputVerification(False, reason="output file is empty")
    return OutputVerification(True, resolved_path=str(resolved), size_bytes=size)
