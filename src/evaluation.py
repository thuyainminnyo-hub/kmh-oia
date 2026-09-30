"""Evaluation boundary for KMH OIA runtime results."""

from dataclasses import dataclass
from typing import Protocol

from src.tools import ToolResult


@dataclass(frozen=True)
class EvaluationResult:
    accepted: bool
    reason: str


class Evaluator(Protocol):
    """Validation boundary between tool execution and response emission."""

    def evaluate(self, result: ToolResult) -> EvaluationResult: ...


class DeterministicEvaluator:
    """Accept only successful governed-tool results."""

    def evaluate(self, result: ToolResult) -> EvaluationResult:
        if not result.success:
            return EvaluationResult(False, result.reason)
        return EvaluationResult(True, "tool result accepted")
