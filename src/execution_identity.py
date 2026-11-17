"""Canonical identity model for multi-account, multi-instance OIA execution."""
from __future__ import annotations
import hashlib,json
from dataclasses import dataclass
@dataclass(frozen=True)
class ExecutionIdentity:
    account_id:str; instance_id:str; environment_id:str; session_id:str
    def __post_init__(self):
        for name in ("account_id","instance_id","environment_id","session_id"):
            value=getattr(self,name)
            if not isinstance(value,str) or not value.strip(): raise ValueError(f"{name} is required")
    def provenance(self)->dict[str,str]:
        return {name:getattr(self,name).strip() for name in ("account_id","instance_id","environment_id","session_id")}
    @property
    def key(self)->str:
        payload=json.dumps(self.provenance(),sort_keys=True,separators=(",",":"))
        return "sha256:"+hashlib.sha256(payload.encode("utf-8")).hexdigest()
@dataclass(frozen=True)
class ExecutionIdentityContext:
    identity:ExecutionIdentity
    command_id:str
    execution_id:str
    job_id:str|None=None
    def __post_init__(self):
        if not isinstance(self.identity,ExecutionIdentity): raise TypeError("identity must be an ExecutionIdentity")
        for name in ("command_id","execution_id"):
            value=getattr(self,name)
            if not isinstance(value,str) or not value.strip(): raise ValueError(f"{name} is required")
        if self.job_id is not None and (not isinstance(self.job_id,str) or not self.job_id.strip()):
            raise ValueError("job_id must be None or a non-empty string")
