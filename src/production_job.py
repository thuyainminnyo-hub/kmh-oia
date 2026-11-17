"""Typed job contract for the local AI production pilot."""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Literal
from uuid import uuid4
from src.execution_identity import ExecutionIdentity, ExecutionIdentityContext

AssetType = Literal["image", "video"]
JobStatus = Literal["queued", "running", "qa_pending", "approved", "rejected", "failed"]

@dataclass(frozen=True)
class ProductionJob:
    job_id: str
    asset_type: AssetType
    prompt: str
    status: JobStatus = "queued"
    attempt: int = 0
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    output_path: str = ""
    error_message: str = ""
    provider_execution_id: str | None = None
    execution_context: ExecutionIdentityContext | None = None

    @classmethod
    def create(cls, asset_type: AssetType, prompt: str, *, execution_identity: ExecutionIdentity | None = None,
               command_id: str | None = None, execution_id: str | None = None) -> "ProductionJob":
        job_id = str(uuid4())
        context = None
        if execution_identity is not None:
            context = ExecutionIdentityContext(execution_identity, command_id or job_id, execution_id or str(uuid4()))
        elif command_id is not None or execution_id is not None:
            raise ValueError("execution_identity is required when execution IDs are supplied")
        return cls(job_id=job_id, asset_type=asset_type, prompt=prompt, execution_context=context)

    def __post_init__(self) -> None:
        if not isinstance(self.job_id, str) or not self.job_id.strip(): raise ValueError("job_id must not be empty")
        if self.asset_type not in {"image", "video"}: raise ValueError("asset_type must be 'image' or 'video'")
        if not isinstance(self.prompt, str) or not self.prompt.strip(): raise ValueError("prompt must not be empty")
        if self.status not in {"queued", "running", "qa_pending", "approved", "rejected", "failed"}: raise ValueError("unsupported production job status")
        if isinstance(self.attempt, bool) or not isinstance(self.attempt, int) or self.attempt < 0: raise ValueError("attempt must be a non-negative integer")
        if not isinstance(self.created_at, str) or not self.created_at.strip(): raise ValueError("created_at must be an ISO-8601 timestamp")
        try: timestamp = datetime.fromisoformat(self.created_at.replace("Z", "+00:00"))
        except ValueError as exc: raise ValueError("created_at must be an ISO-8601 timestamp") from exc
        if timestamp.tzinfo is None or timestamp.utcoffset() is None: raise ValueError("created_at must include a timezone")
        if not isinstance(self.output_path, str): raise ValueError("output_path must be a string")
        if self.status == "approved" and not self.output_path.strip(): raise ValueError("approved jobs must include output_path")
        if not isinstance(self.error_message, str): raise ValueError("error_message must be a string")
        if self.provider_execution_id is not None and (not isinstance(self.provider_execution_id, str) or not self.provider_execution_id.strip()):
            raise ValueError("provider_execution_id must be None or a non-empty string")
        if self.execution_context is not None and not isinstance(self.execution_context, ExecutionIdentityContext):
            raise TypeError("execution_context must be an ExecutionIdentityContext")
