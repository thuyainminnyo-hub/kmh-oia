"""Snapshot-backed evidence admission gate; QA remains pending."""
import os
from pathlib import Path
from src.execution_identity import ExecutionIdentityContext
from src.production_evidence import ProductionEvidence
from src.production_audit import JsonlProductionAuditSink
from src.verified_snapshot_store import VerifiedArtifactStore

def create_verified_evidence(*,job_id:str,adapter_name:str,output_path:str,allowed_output_root:str|Path,
    elapsed_ms:int,provider_execution_id:str|None,execution_context:ExecutionIdentityContext,
    snapshot_store:VerifiedArtifactStore,audit_sink:JsonlProductionAuditSink|None=None)->ProductionEvidence:
    if not isinstance(execution_context,ExecutionIdentityContext): raise ValueError("execution identity context is required for evidence")
    if execution_context.job_id!=job_id: raise ValueError("execution context job_id does not match evidence job_id")
    allowed_root_path=Path(allowed_output_root).expanduser().resolve(strict=True)
    source_path=Path(output_path).expanduser()
    if not source_path.is_absolute(): source_path=allowed_root_path/source_path
    # Record the same lexical path interpretation used by snapshot admission.
    # Do not resolve symlinks after ingestion: that could record a different target
    # from the inode whose bytes were actually snapshotted.
    recorded_output_path=str(Path(os.path.abspath(source_path)))
    snapshot=snapshot_store.put_verified(output_path,allowed_root=allowed_root_path,artifact_id=f"job-{job_id}")
    snapshot_payload=snapshot_store.get_verified(snapshot)
    if len(snapshot_payload)!=snapshot.size_bytes: raise ValueError("retrieved snapshot size does not match evidence")
    evidence=ProductionEvidence.from_snapshot(job_id=job_id,adapter_name=adapter_name,output_path=recorded_output_path,
        snapshot=snapshot,elapsed_ms=elapsed_ms,provider_execution_id=provider_execution_id,context=execution_context)
    if audit_sink is not None: audit_sink.record_evidence(evidence,snapshot_store=snapshot_store)
    return evidence
