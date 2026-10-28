"""Execution bridge contract for local AI production jobs.

The bridge coordinates an injected adapter and verifies reported artifacts
inside an explicitly allowed output root. It does not implement a model provider.
"""
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Protocol

from src.output_verification import verify_output_file
from src.production_job import ProductionJob


@dataclass(frozen=True)
class AdapterResult:
    success: bool
    output_path: str = ""
    error_message: str = ""


class ProductionAdapter(Protocol):
    """Provider boundary for a local model or workflow runner."""

    def execute(self, job: ProductionJob) -> AdapterResult: ...


class ProductionExecutionBridge:
    """Run a job and fail closed unless its artifact is verified in the allowed root."""

    def __init__(self, adapter: ProductionAdapter, *, allowed_output_root: str | Path) -> None:
        self.adapter = adapter
        self.allowed_output_root = Path(allowed_output_root).resolve()

    def execute(self, job: ProductionJob) -> ProductionJob:
        if job.status != "queued":
            raise ValueError("only queued jobs can be executed")
        running = replace(job, status="running", attempt=job.attempt + 1)
        try:
            result = self.adapter.execute(running)
        except Exception as exc:
            return replace(
                running,
                status="failed",
                error_message=f"adapter raised {type(exc).__name__}: {exc}",
            )

        if not isinstance(result, AdapterResult):
            return replace(
                running, status="failed",
                error_message="adapter returned an invalid result type",
            )
        if not result.success:
            return replace(
                running,
                status="failed",
                error_message=result.error_message or "adapter reported failure",
            )
        verification = verify_output_file(result.output_path, self.allowed_output_root)
        if not verification.verified:
            return replace(
                running,
                status="failed",
                output_path=result.output_path if isinstance(result.output_path, str) else "",
                error_message=f"output verification failed: {verification.reason}",
            )
        return replace(
            running,
            status="qa_pending",
            output_path=verification.resolved_path or "",
            error_message="",
        )
