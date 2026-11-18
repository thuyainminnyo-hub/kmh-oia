"""Execution bridge contract for local AI production jobs.

The bridge returns the PNG integrity result alongside the job so evidence
creation can consume the exact verified bytes rather than reopening a path.
"""
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Protocol

from src.image_integrity import ImageIntegrityResult, verify_png_integrity
from src.output_verification import verify_output_file
from src.production_job import ProductionJob


@dataclass(frozen=True)
class AdapterResult:
    success: bool
    output_path: str = ""
    error_message: str = ""
    provider_execution_id: str | None = None


class ProductionAdapter(Protocol):
    """Provider boundary for a local model or workflow runner."""

    def execute(self, job: ProductionJob) -> AdapterResult: ...


class ProductionExecutionBridge:
    """Run a job and fail closed unless its artifact is verified in the allowed root."""

    def __init__(self, adapter: ProductionAdapter, *, allowed_output_root: str | Path) -> None:
        self.adapter = adapter
        self.allowed_output_root = Path(allowed_output_root).resolve()

    def execute(self, job: ProductionJob) -> ProductionJob:
        """Backward-compatible job-only interface."""
        result, _integrity = self.execute_with_integrity(job)
        return result

    def execute_with_integrity(
        self, job: ProductionJob
    ) -> tuple[ProductionJob, ImageIntegrityResult | None]:
        """Return the completed job plus the exact verified PNG bytes, if applicable."""
        if job.status != "queued":
            raise ValueError("only queued jobs can be executed")
        running = replace(job, status="running", attempt=job.attempt + 1)
        try:
            result = self.adapter.execute(running)
        except Exception as exc:
            return replace(
                running, status="failed",
                error_message=f"adapter raised {type(exc).__name__}: {exc}",
            ), None

        if not isinstance(result, AdapterResult):
            return replace(
                running, status="failed",
                error_message="adapter returned an invalid result type",
            ), None
        if not result.success:
            return replace(
                running, status="failed",
                error_message=result.error_message or "adapter reported failure",
            ), None
        verification = verify_output_file(result.output_path, self.allowed_output_root)
        if not verification.verified:
            return replace(
                running, status="failed",
                output_path=result.output_path if isinstance(result.output_path, str) else "",
                error_message=f"output verification failed: {verification.reason}",
            ), None

        integrity: ImageIntegrityResult | None = None
        if running.asset_type == "image":
            integrity = verify_png_integrity(
                verification.resolved_path or "", self.allowed_output_root
            )
            if not integrity.verified:
                return replace(
                    running, status="failed",
                    output_path=verification.resolved_path or "",
                    error_message=f"image integrity verification failed: {integrity.reason}",
                ), None
            if (
                integrity.verified_bytes is None
                or integrity.sha256 is None
                or integrity.size_bytes != len(integrity.verified_bytes)
            ):
                return replace(
                    running, status="failed",
                    output_path=verification.resolved_path or "",
                    error_message="image integrity verifier did not retain verified bytes",
                ), None

        if result.provider_execution_id is not None and (
            not isinstance(result.provider_execution_id, str) or not result.provider_execution_id.strip()
        ):
            return replace(
                running, status="failed",
                error_message="adapter returned an invalid provider_execution_id",
            ), None
        return replace(
            running,
            status="qa_pending",
            output_path=verification.resolved_path or "",
            error_message="",
            provider_execution_id=result.provider_execution_id,
        ), integrity
