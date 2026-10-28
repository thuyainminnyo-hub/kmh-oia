"""Typed job contract for the local AI production pilot.

This module defines the job envelope only; it does not execute models or
claim that an asset has been generated or externally validated.
"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Literal
from uuid import uuid4


AssetType = Literal["image", "video"]
JobStatus = Literal["queued", "running", "qa_pending", "approved", "rejected", "failed"]


@dataclass(frozen=True)
class ProductionJob:
    """Immutable, validated request/result envelope for one production job."""

    job_id: str
    asset_type: AssetType
    prompt: str
    status: JobStatus = "queued"
    attempt: int = 0
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    output_path: str = ""
    error_message: str = ""

    @classmethod
    def create(cls, asset_type: AssetType, prompt: str) -> "ProductionJob":
        """Create a queued job with a generated identifier and UTC timestamp."""
        return cls(job_id=str(uuid4()), asset_type=asset_type, prompt=prompt)

    def __post_init__(self) -> None:
        if not isinstance(self.job_id, str) or not self.job_id.strip():
            raise ValueError("job_id must not be empty")
        if self.asset_type not in {"image", "video"}:
            raise ValueError("asset_type must be 'image' or 'video'")
        if not isinstance(self.prompt, str) or not self.prompt.strip():
            raise ValueError("prompt must not be empty")
        if self.status not in {
            "queued", "running", "qa_pending", "approved", "rejected", "failed"
        }:
            raise ValueError("unsupported production job status")
        if isinstance(self.attempt, bool) or not isinstance(self.attempt, int) or self.attempt < 0:
            raise ValueError("attempt must be a non-negative integer")
        if not isinstance(self.created_at, str) or not self.created_at.strip():
            raise ValueError("created_at must be an ISO-8601 timestamp")
        try:
            timestamp = datetime.fromisoformat(self.created_at.replace("Z", "+00:00"))
        except ValueError as exc:
            raise ValueError("created_at must be an ISO-8601 timestamp") from exc
        if timestamp.tzinfo is None or timestamp.utcoffset() is None:
            raise ValueError("created_at must include a timezone")
        if not isinstance(self.output_path, str):
            raise ValueError("output_path must be a string")
        if self.status == "approved" and not self.output_path.strip():
            raise ValueError("approved jobs must include output_path")
        if not isinstance(self.error_message, str):
            raise ValueError("error_message must be a string")
