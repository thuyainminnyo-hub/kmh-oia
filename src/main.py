"""Executable KMH OIA text-path runtime with session state."""

from dataclasses import dataclass

from src.security import ToolSecurityPolicy
from src.state import StateStore


@dataclass
class Trace:
    stages: list[str]


def run(
    goal: str,
    session_id: str = "default",
    state: StateStore | None = None,
    security: ToolSecurityPolicy | None = None,
    tool_name: str = "echo",
) -> tuple[str, Trace]:
    if not goal.strip():
        raise ValueError("goal must not be empty")

    state = state or StateStore()
    security = security or ToolSecurityPolicy()
    trace = Trace(stages=[])

    trace.stages.append("input_gateway")
    trace.stages.append("oia_core")
    context = {"goal": goal.strip()}
    trace.stages.append("context_assembly")
    trace.stages.append("workflow")
    trace.stages.append("agent")

    state.set(session_id, "last_goal", context["goal"])
    trace.stages.append("state")

    decision = security.authorize(tool_name)
    trace.stages.append("tool_security")
    if not decision.allowed:
        raise PermissionError(decision.reason)

    # Governed tool: deterministic local transformation for the first slice.
    tool_output = context["goal"].strip()
    trace.stages.append("governed_tool")

    evaluation = bool(tool_output)
    trace.stages.append("evaluation")

    response = tool_output
    trace.stages.append("response")
    trace.stages.append("trace")

    if not evaluation:
        raise RuntimeError("evaluation failed")

    return response, trace


if __name__ == "__main__":
    import sys

    goal = " ".join(sys.argv[1:]).strip()
    response, trace = run(goal)
    print(response)
    print("TRACE:", " -> ".join(trace.stages))
