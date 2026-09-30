"""Standardized runtime failure boundary for KMH OIA."""

from dataclasses import dataclass
from enum import Enum
from typing import Protocol


class ErrorCategory(str, Enum):
    VALIDATION = "validation"
    AUTHORIZATION = "authorization"
    EXECUTION = "execution"
    EVALUATION = "evaluation"
    INTERNAL = "internal"


@dataclass(frozen=True)
class RuntimeErrorInfo:
    category: ErrorCategory
    message: str
    recoverable: bool


class ErrorBoundary(Protocol):
    """Boundary that normalizes runtime exceptions into structured failures."""

    def classify(self, error: Exception) -> RuntimeErrorInfo: ...


class DeterministicErrorBoundary:
    """Map known runtime exceptions to stable error categories."""

    def classify(self, error: Exception) -> RuntimeErrorInfo:
        if isinstance(error, ValueError):
            return RuntimeErrorInfo(ErrorCategory.VALIDATION, str(error), False)
        if isinstance(error, PermissionError):
            return RuntimeErrorInfo(ErrorCategory.AUTHORIZATION, str(error), False)
        return RuntimeErrorInfo(ErrorCategory.INTERNAL, str(error), False)
