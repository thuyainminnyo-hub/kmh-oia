"""Execution-boundary helper for creating evidence after verified output.

This helper composes the existing output-root verification with the evidence
manifest. It intentionally leaves QA pending and does not persist evidence.
"""
from __future__ import annotations

from pathlib import Path

from src.output_verification import verify_output_file
from src.production_evidence import ProductionEvidence


def create_verified_evidence(
    *,
    job_id: str,
    adapter_name: str,
    output_path: str,
    allowed_output_root: str | Path,
    elapsed_ms: int,
    provider_execution_id: str | None = None,
) -> ProductionEvidence:
    """Require output-root verification before hashing an output into evidence."""
    verification = verify_output_file(output_path, allowed_output_root)
    if not verification.verified or not verification.resolved_path:
        raise ValueError(f"output verification failed: {verification.reason}")
    return ProductionEvidence.from_output(
        job_id=job_id,
        adapter_name=adapter_name,
        output_path=verification.resolved_path,
        elapsed_ms=elapsed_ms,
        provider_execution_id=provider_execution_id,
        qa_decision="pending",
    )
