"""Explicit core and workflow boundaries for the KMH OIA runtime."""

from typing import Protocol

from src.agent import AgentDecision, AgentRequest


class OIACore(Protocol):
    """Boundary for assembling a normalized runtime goal."""

    def build_context(self, goal: str) -> dict[str, str]: ...


class Workflow(Protocol):
    """Boundary for selecting the next agent decision input."""

    def prepare(self, context: dict[str, str]) -> AgentRequest: ...


class DeterministicOIACore:
    """Minimal deterministic core implementation."""

    def build_context(self, goal: str) -> dict[str, str]:
        return {"goal": goal}


class DeterministicWorkflow:
    """Minimal deterministic workflow implementation."""

    def prepare(self, context: dict[str, str]) -> AgentRequest:
        return AgentRequest(context["goal"])


def decision_summary(decision: AgentDecision) -> dict[str, str]:
    """Expose a small typed-compatible summary for tracing/integration."""
    return {"tool": decision.tool_name, "reason": decision.reason}
