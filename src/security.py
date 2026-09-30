"""Minimal deterministic security policy for governed tool calls."""

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class ToolDecision:
    allowed: bool
    reason: str


class SecurityPolicy(Protocol):
    """Authorization boundary for governed tool calls."""

    def authorize(self, tool_name: str) -> ToolDecision: ...


class ToolSecurityPolicy:
    """Allow only explicitly registered deterministic tools."""

    def __init__(self, allowed_tools: set[str] | None = None) -> None:
        self._allowed_tools = allowed_tools or {"echo"}

    def authorize(self, tool_name: str) -> ToolDecision:
        if not tool_name.strip():
            return ToolDecision(False, "tool_name must not be empty")
        if tool_name not in self._allowed_tools:
            return ToolDecision(False, "tool is not allowlisted")
        return ToolDecision(True, "tool is allowlisted")
