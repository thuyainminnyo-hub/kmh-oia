"""Evidence manifest for completed local-AI production jobs.

The manifest records file integrity and execution metadata; it does not assess
visual quality, policy compliance, or whether the asset satisfies its brief.
"""
from __future__ import annotations

import hashlib
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Literal
import json


QADecision = Literal["pending", "approved", "rejected"]


@dataclass(frozen=True)
class ProductionEvidence:
    job_id: str
    adapter_name: str
    output_path: str
    output_sha256: str
    output_size_bytes: int
    elapsed_ms: int
    provider_execution_id: str | None
    qa_decision: QADecision = "pending"

    def __post_init__(self) -> None:
        for name in ("job_id", "adapter_name", "output_path", "output_sha256"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be a non-empty string")
        if len(self.output_sha256) != 64 or any(
            c not in "0123456789abcdef" for c in self.output_sha256
        ):
            raise ValueError("output_sha256 must be a lowercase SHA-256 hex digest")
        if isinstance(self.output_size_bytes, bool) or not isinstance(self.output_size_bytes, int) or self.output_size_bytes <= 0:
            raise ValueError("output_size_bytes must be a positive integer")
        if isinstance(self.elapsed_ms, bool) or not isinstance(self.elapsed_ms, int) or self.elapsed_ms < 0:
            raise ValueError("elapsed_ms must be a non-negative integer")
        if self.provider_execution_id is not None and (
            not isinstance(self.provider_execution_id, str) or not self.provider_execution_id.strip()
        ):
            raise ValueError("provider_execution_id must be None or a non-empty string")
        if self.qa_decision not in {"pending", "approved", "rejected"}:
            raise ValueError("qa_decision must be pending, approved, or rejected")

    @classmethod
    def from_output(
        cls,
        *,
        job_id: str,
        adapter_name: str,
        output_path: str | Path,
        elapsed_ms: int,
        provider_execution_id: str | None = None,
        qa_decision: QADecision = "pending",
    ) -> "ProductionEvidence":
        path = Path(output_path).resolve(strict=True)
        if not path.is_file():
            raise ValueError("output_path must refer to a regular file")
        size = path.stat().st_size
        if size <= 0:
            raise ValueError("output file must not be empty")
        digest = hashlib.sha256()
        with path.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
        return cls(
            job_id=job_id,
            adapter_name=adapter_name,
            output_path=str(path),
            output_sha256=digest.hexdigest(),
            output_size_bytes=size,
            elapsed_ms=elapsed_ms,
            provider_execution_id=provider_execution_id,
            qa_decision=qa_decision,
        )

    def to_json(self) -> str:
        """Return a stable, newline-terminated JSON representation."""
        return json.dumps(asdict(self), sort_keys=True, indent=2) + "\n"
