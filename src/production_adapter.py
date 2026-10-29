"""Contracts for executing local-AI production jobs.

This module defines an adapter boundary only. FakeProductionAdapter never
invokes a model and never creates an output file.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from src.production_job import ProductionJob


@dataclass(frozen=True)
class ExecutionResult:
    """A normalized result returned by a production execution adapter."""

    success: bool
    adapter_name: str
    output_ref: str | None = None
    error_message: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.success, bool):
            raise TypeError("success must be a bool")
        if not isinstance(self.adapter_name, str) or not self.adapter_name.strip():
            raise ValueError("adapter_name must be a non-empty string")
        if self.output_ref is not None and (
            not isinstance(self.output_ref, str) or not self.output_ref.strip()
        ):
            raise ValueError("output_ref must be None or a non-empty string")
        if self.error_message is not None and (
            not isinstance(self.error_message, str) or not self.error_message.strip()
        ):
            raise ValueError("error_message must be None or a non-empty string")
        if self.success and not self.output_ref:
            raise ValueError("successful execution requires output_ref")
        if self.success and self.error_message:
            raise ValueError("successful execution cannot include error_message")
        if not self.success and not self.error_message:
            raise ValueError("failed execution requires error_message")
        if not self.success and self.output_ref:
            raise ValueError("failed execution cannot include output_ref")


class ProductionAdapter(Protocol):
    """Structural interface implemented by a real or fake executor."""

    @property
    def name(self) -> str:
        """Stable adapter identifier used in audit records."""

    def execute(self, job: ProductionJob) -> ExecutionResult:
        """Execute a job and return a normalized result."""


class FakeProductionAdapter:
    """Deterministic test adapter; it does not run a model or write files."""

    @property
    def name(self) -> str:
        return "fake"

    def __init__(self, *, fail_with: str | None = None) -> None:
        if fail_with is not None and (
            not isinstance(fail_with, str) or not fail_with.strip()
        ):
            raise ValueError("fail_with must be None or a non-empty string")
        self._fail_with = fail_with

    def execute(self, job: ProductionJob) -> ExecutionResult:
        if not isinstance(job, ProductionJob):
            raise TypeError("job must be a ProductionJob")
        if self._fail_with:
            return ExecutionResult(
                success=False,
                adapter_name=self.name,
                error_message=self._fail_with,
            )
        return ExecutionResult(
            success=True,
            adapter_name=self.name,
            output_ref=f"fake://outputs/{job.job_id}.{job.asset_type}",
        )
