"""Explicit component boundaries for the first KMH OIA runtime slice."""

from dataclasses import dataclass

from src.security import ToolSecurityPolicy
from src.state import StateStore


@dataclass(frozen=True)
class RuntimeContext:
    goal: str


class InputGateway:
    def accept(self, goal: str) -> RuntimeContext:
        if not goal.strip():
            raise ValueError("goal must not be empty")
        return RuntimeContext(goal=goal.strip())


class ContextAssembly:
    def build(self, context: RuntimeContext) -> dict[str, str]:
        return {"goal": context.goal}


class GovernedTool:
    def __init__(self, security: ToolSecurityPolicy | None = None) -> None:
        self.security = security or ToolSecurityPolicy()

    def execute(self, tool_name: str, goal: str) -> str:
        decision = self.security.authorize(tool_name)
        if not decision.allowed:
            raise PermissionError(decision.reason)
        return goal


class OIARuntime:
    def __init__(self, state: StateStore | None = None, security: ToolSecurityPolicy | None = None) -> None:
        self.state = state or StateStore()
        self.gateway = InputGateway()
        self.context = ContextAssembly()
        self.tool = GovernedTool(security)

    def execute(self, goal: str, session_id: str = "default", tool_name: str = "echo") -> tuple[str, list[str]]:
        stages: list[str] = ["input_gateway"]
        accepted = self.gateway.accept(goal)
        stages.append("oia_core")
        context = self.context.build(accepted)
        stages.append("context_assembly")
        stages.extend(["workflow", "agent"])
        self.state.set(session_id, "last_goal", context["goal"])
        stages.append("state")
        output = self.tool.execute(tool_name, context["goal"])
        stages.extend(["tool_security", "governed_tool", "evaluation", "response", "trace"])
        return output, stages
