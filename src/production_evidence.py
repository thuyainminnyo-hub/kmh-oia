"""Immutable provenance manifest for a verified production artifact."""
from __future__ import annotations
import json
from dataclasses import asdict,dataclass
from typing import Literal
from src.execution_identity import ExecutionIdentityContext
from src.verified_snapshot_store import VerifiedSnapshot
QADecision=Literal["pending","approved","rejected"]
@dataclass(frozen=True)
class ProductionEvidence:
    job_id:str; adapter_name:str; output_path:str; output_sha256:str
    output_size_bytes:int; elapsed_ms:int; provider_execution_id:str|None
    snapshot_reference:str; artifact_id:str; execution_id:str; command_id:str
    identity_key:str; verification_version:str; qa_decision:QADecision="pending"
    def __post_init__(self):
        for name in ("job_id","adapter_name","output_path","output_sha256","snapshot_reference","artifact_id","execution_id","command_id","identity_key","verification_version"):
            value=getattr(self,name)
            if not isinstance(value,str) or not value.strip(): raise ValueError(f"{name} must be a non-empty string")
        if len(self.output_sha256)!=64 or any(c not in "0123456789abcdef" for c in self.output_sha256): raise ValueError("output_sha256 must be a lowercase SHA-256 hex digest")
        if isinstance(self.output_size_bytes,bool) or not isinstance(self.output_size_bytes,int) or self.output_size_bytes<=0: raise ValueError("output_size_bytes must be a positive integer")
        if isinstance(self.elapsed_ms,bool) or not isinstance(self.elapsed_ms,int) or self.elapsed_ms<0: raise ValueError("elapsed_ms must be a non-negative integer")
        if self.provider_execution_id is not None and (not isinstance(self.provider_execution_id,str) or not self.provider_execution_id.strip()): raise ValueError("provider_execution_id must be None or a non-empty string")
        if self.qa_decision != "pending": raise ValueError("evidence admission must remain pending; record QA decisions through the audit sink")
        if self.artifact_id != f"job-{self.job_id}": raise ValueError("artifact_id does not match evidence job_id")
        expected_snapshot_reference = f"sha256/{self.output_sha256[:2]}/{self.output_sha256[2:4]}/{self.output_sha256}"
        if self.snapshot_reference != expected_snapshot_reference: raise ValueError("snapshot_reference does not match evidence digest")
        if len(self.identity_key) != 71 or not self.identity_key.startswith("sha256:") or any(c not in "0123456789abcdef" for c in self.identity_key[7:]):
            raise ValueError("identity_key must be a SHA-256 execution identity key")
    @classmethod
    def from_snapshot(cls,*,job_id:str,adapter_name:str,output_path:str,snapshot:VerifiedSnapshot,elapsed_ms:int,
                      provider_execution_id:str|None,context:ExecutionIdentityContext)->"ProductionEvidence":
        if not isinstance(snapshot,VerifiedSnapshot): raise TypeError("snapshot must be a VerifiedSnapshot")
        if snapshot.artifact_id!=f"job-{job_id}": raise ValueError("snapshot artifact_id does not match evidence job_id")
        if not isinstance(context,ExecutionIdentityContext): raise TypeError("context must be an ExecutionIdentityContext")
        if context.job_id!=job_id: raise ValueError("execution context job_id does not match evidence job_id")
        return cls(job_id,adapter_name,output_path,snapshot.sha256,snapshot.size_bytes,elapsed_ms,provider_execution_id,
                   snapshot.storage_key,snapshot.artifact_id,context.execution_id,context.command_id,context.identity.key,
                   snapshot.verification_version,"pending")
    def to_json(self)->str: return json.dumps(asdict(self),sort_keys=True,indent=2)+"\n"
