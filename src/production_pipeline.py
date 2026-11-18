"""Compose execution, verified snapshot admission, evidence, and audit."""
from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path
from time import monotonic

from src.production_audit import JsonlProductionAuditSink
from src.production_evidence import ProductionEvidence
from src.production_evidence_gate import create_verified_evidence
from src.production_execution import ProductionExecutionBridge
from src.production_job import ProductionJob
from src.verified_snapshot_store import VerifiedArtifactStore


@dataclass(frozen=True)
class ProductionPipelineResult:
    job: ProductionJob
    evidence: ProductionEvidence | None


def execute_with_evidence(
    job: ProductionJob,
    *,
    bridge: ProductionExecutionBridge,
    adapter_name: str,
    allowed_output_root: str | Path,
    audit_sink: JsonlProductionAuditSink,
    snapshot_store: VerifiedArtifactStore | None = None,
    provider_execution_id: str | None = None,
) -> ProductionPipelineResult:
    """Run one job and create evidence bound to the exact verified output bytes."""
    started = monotonic()
    executed, integrity = bridge.execute_with_integrity(job)
    if executed.status != "qa_pending":
        return ProductionPipelineResult(job=executed, evidence=None)

    elapsed_ms = max(0, int((monotonic() - started) * 1000))
    try:
        effective_provider_id = provider_execution_id or executed.provider_execution_id
        if executed.asset_type == "image":
            if integrity is None or not integrity.verified:
                raise ValueError("image job is missing its successful PNG integrity result")
            if integrity.resolved_path != executed.output_path:
                raise ValueError("PNG integrity path does not match executed output path")
            if integrity.verified_bytes is None or integrity.sha256 is None:
                raise ValueError("PNG integrity result is missing verified bytes or digest")
            if snapshot_store is None:
                raise ValueError("image evidence requires a verified snapshot store")
            if provider_execution_id is not None and provider_execution_id != executed.provider_execution_id:
                raise ValueError("caller provider_execution_id cannot override adapter attribution")
            evidence = create_verified_evidence(
                job_id=executed.job_id,
                adapter_name=adapter_name,
                output_path=executed.output_path,
                allowed_output_root=allowed_output_root,
                elapsed_ms=elapsed_ms,
                provider_execution_id=effective_provider_id,
                audit_sink=audit_sink,
                verified_bytes=integrity.verified_bytes,
                expected_sha256=integrity.sha256,
                expected_size_bytes=integrity.size_bytes,
                snapshot_store=snapshot_store,
            )
        else:
            evidence = create_verified_evidence(
                job_id=executed.job_id,
                adapter_name=adapter_name,
                output_path=executed.output_path,
                allowed_output_root=allowed_output_root,
                elapsed_ms=elapsed_ms,
                provider_execution_id=effective_provider_id,
                audit_sink=audit_sink,
            )
    except Exception as exc:
        failed = replace(
            executed,
            status="failed",
            error_message=f"evidence/audit recording failed: {type(exc).__name__}: {exc}",
        )
        return ProductionPipelineResult(job=failed, evidence=None)
    return ProductionPipelineResult(job=executed, evidence=evidence)
