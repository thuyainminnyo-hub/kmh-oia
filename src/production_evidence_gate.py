"""Snapshot-backed evidence admission gate; QA remains pending."""
from pathlib import Path
from src.execution_identity import ExecutionIdentityContext
from src.production_evidence import ProductionEvidence
from src.production_audit import JsonlProductionAuditSink
from src.verified_snapshot_store import VerifiedArtifactStore

def create_verified_evidence(*, job_id: str, adapter_name: str, output_path: str,
    allowed_output_root: str | Path, elapsed_ms: int, provider_execution_id: str | None,
    execution_context: ExecutionIdentityContext, snapshot_store: VerifiedArtifactStore,
    audit_sink: JsonlProductionAuditSink | None = None) -> ProductionEvidence:
    if not isinstance(execution_context, ExecutionIdentityContext):
        raise ValueError("execution identity context is required for evidence")
    snapshot = snapshot_store.put_verified(output_path, allowed_root=allowed_output_root, artifact_id=f"job-{job_id}")
    snapshot_store.verify(snapshot)
    evidence = ProductionEvidence.from_snapshot(job_id=job_id, adapter_name=adapter_name,
        output_path=str(Path(output_path).resolve()), snapshot=snapshot, elapsed_ms=elapsed_ms,
        provider_execution_id=provider_execution_id, context=execution_context)
    if audit_sink is not None: audit_sink.record_evidence(evidence)
    return evidence
