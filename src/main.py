"""Executable KMH OIA text-path runtime with explicit component composition."""

from dataclasses import dataclass

from src.components import OIARuntime
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
    runtime = OIARuntime(state=state, security=security)
    response, stages = runtime.execute(
        goal,
        session_id=session_id,
        tool_name=tool_name,
    )
    return response, Trace(stages=stages)


if __name__ == "__main__":
    import sys

    goal = " ".join(sys.argv[1:]).strip()
    response, trace = run(goal)
    print(response)
    print("TRACE:", " -> ".join(trace.stages))
