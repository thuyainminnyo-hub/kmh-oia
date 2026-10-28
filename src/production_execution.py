"""Execution bridge contract for local AI production jobs.

The bridge coordinates an injected adapter and verifies that its reported
artifact exists. It does not implement a model provider itself.
"""
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Protocol

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
    """Run a job through an adapter and fail closed on missing artifacts."""

    def __init__(self, adapter: ProductionAdapter) -> None:
        self.adapter = adapter

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

        if not result.success:
            return replace(
                running,
                status="failed",
                output_path=result.output_path,
                error_message=result.error_message or "adapter reported failure",
            )
        if not isinstance(result.output_path, str) or not result.output_path.strip():
            return replace(
                running,
                status="failed",
                error_message="adapter reported success without an output path",
            )
        if not Path(result.output_path).is_file():
            return replace(
                running,
                status="failed",
                output_path=result.output_path,
                error_message="reported artifact does not exist as a file",
            )
        return replace(
            running,
            status="qa_pending",
            output_path=result.output_path,
            error_message="",
        )
