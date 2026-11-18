"""Evidence admission gate with immutable verified-byte binding."""
from __future__ import annotations

from pathlib import Path

from src.output_verification import verify_output_file
from src.production_evidence import ProductionEvidence
from src.production_audit import JsonlProductionAuditSink
from src.verified_snapshot_store import VerifiedArtifactStore


def create_verified_evidence(
    *,
    job_id: str,
    adapter_name: str,
    output_path: str,
    allowed_output_root: str | Path,
    elapsed_ms: int,
    provider_execution_id: str | None = None,
    audit_sink: JsonlProductionAuditSink | None = None,
    verified_bytes: bytes | None = None,
    expected_sha256: str | None = None,
    expected_size_bytes: int | None = None,
    snapshot_store: VerifiedArtifactStore | None = None,
) -> ProductionEvidence:
    """Create evidence only after binding it to the bytes verified upstream.

    The PNG execution path supplies all four verified-byte arguments. The
    legacy path-only route remains for non-PNG/legacy callers and is not used
    by the image pipeline.
    """
    supplied = (
        verified_bytes is not None,
        expected_sha256 is not None,
        expected_size_bytes is not None,
        snapshot_store is not None,
    )
    if any(supplied):
        if not all(supplied):
            raise ValueError("verified bytes, digest, size, and snapshot store are all required")
        if not isinstance(verified_bytes, bytes) or not verified_bytes:
            raise ValueError("verified bytes must be non-empty bytes")
        snapshot = snapshot_store.put_bytes(
            verified_bytes,
            artifact_id=f"job-{job_id}",
            expected_sha256=expected_sha256,
            expected_size_bytes=expected_size_bytes,
        )
        evidence = ProductionEvidence.from_snapshot(
            job_id=job_id,
            adapter_name=adapter_name,
            output_path=output_path,
            snapshot=snapshot,
            elapsed_ms=elapsed_ms,
            provider_execution_id=provider_execution_id,
        )
        if evidence.output_sha256 != expected_sha256 or evidence.output_size_bytes != expected_size_bytes:
            raise ValueError("snapshot digest/size does not match PNG integrity result")
    else:
        verification = verify_output_file(output_path, allowed_output_root)
        if not verification.verified or not verification.resolved_path:
            raise ValueError(f"output verification failed: {verification.reason}")
        evidence = ProductionEvidence.from_output(
            job_id=job_id,
            adapter_name=adapter_name,
            output_path=verification.resolved_path,
            elapsed_ms=elapsed_ms,
            provider_execution_id=provider_execution_id,
            qa_decision="pending",
        )

    if audit_sink is not None:
        audit_sink.record_evidence(evidence)
    return evidence
