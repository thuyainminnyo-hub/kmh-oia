"""Compose execution, snapshot admission, evidence creation, and audit logging."""
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

def execute_with_evidence(job: ProductionJob, *, bridge: ProductionExecutionBridge,
    adapter_name: str, allowed_output_root: str | Path, audit_sink: JsonlProductionAuditSink,
    snapshot_store: VerifiedArtifactStore, provider_execution_id: str | None = None) -> ProductionPipelineResult:
    started=monotonic(); executed=bridge.execute(job)
    if executed.status!="qa_pending": return ProductionPipelineResult(job=executed,evidence=None)
    elapsed_ms=max(0,int((monotonic()-started)*1000))
    try:
        if executed.execution_context is None: raise ValueError("production job has no execution identity context")
        if provider_execution_id is not None and provider_execution_id!=executed.provider_execution_id:
            raise ValueError("caller provider_execution_id cannot override adapter attribution")
        evidence=create_verified_evidence(job_id=executed.job_id,adapter_name=adapter_name,
            output_path=executed.output_path,allowed_output_root=allowed_output_root,elapsed_ms=elapsed_ms,
            provider_execution_id=executed.provider_execution_id,execution_context=executed.execution_context,
            snapshot_store=snapshot_store,audit_sink=audit_sink)
    except Exception as exc:
        failed=replace(executed,status="failed",error_message=f"evidence/audit recording failed: {type(exc).__name__}: {exc}")
        return ProductionPipelineResult(job=failed,evidence=None)
    return ProductionPipelineResult(job=executed,evidence=evidence)
