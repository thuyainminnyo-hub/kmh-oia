"""Compose execution, output verification, evidence creation, and audit logging.

This orchestration helper does not perform semantic image QA or invoke a model
itself; it uses the injected execution bridge and leaves QA pending.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path
from time import monotonic

from src.production_audit import JsonlProductionAuditSink
from src.production_evidence import ProductionEvidence
from src.production_evidence_gate import create_verified_evidence
from src.production_execution import ProductionExecutionBridge
from src.production_job import ProductionJob


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
    provider_execution_id: str | None = None,
) -> ProductionPipelineResult:
    """Run one queued job and record evidence only for verified output."""
    started = monotonic()
    executed = bridge.execute(job)
    if executed.status != "qa_pending":
        return ProductionPipelineResult(job=executed, evidence=None)

    elapsed_ms = max(0, int((monotonic() - started) * 1000))
    try:
        evidence = create_verified_evidence(
            job_id=executed.job_id,
            adapter_name=adapter_name,
            output_path=executed.output_path,
            allowed_output_root=allowed_output_root,
            elapsed_ms=elapsed_ms,
            provider_execution_id=provider_execution_id,
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
