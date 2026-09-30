"""Agent boundary for the KMH OIA runtime."""

from dataclasses import dataclass, field
from typing import Protocol


@dataclass(frozen=True)
class AgentRequest:
    goal: str
    context: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class AgentDecision:
    tool_name: str
    input_text: str
    reason: str


class Agent(Protocol):
    """Planning boundary between runtime orchestration and an agent implementation."""

    def decide(self, request: AgentRequest) -> AgentDecision: ...


class DeterministicAgent:
    """Minimal agent implementation used until a model-backed agent is required."""

    def decide(self, request: AgentRequest) -> AgentDecision:
        return AgentDecision(
            tool_name="echo",
            input_text=request.goal,
            reason="deterministic default policy",
        )
