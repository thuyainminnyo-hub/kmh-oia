"""Executable KMH OIA text-path runtime with explicit component composition."""

from dataclasses import dataclass

from src.components import OIARuntime
from src.security import ToolSecurityPolicy
from src.state import StateStore, StateStoreContract
from src.trace import TraceEvent, Tracer


@dataclass
class Trace:
    stages: list[str]
    events: list[TraceEvent]


def run(
    goal: str,
    session_id: str = "default",
    state: StateStoreContract | None = None,
    security: ToolSecurityPolicy | None = None,
    tool_name: str = "echo",
    tracer: Tracer | None = None,
) -> tuple[str, Trace]:
    runtime = OIARuntime(state=state, security=security, tracer=tracer)
    response, stages, events = runtime.execute_detailed(
        goal,
        session_id=session_id,
        tool_name=tool_name,
    )
    return response, Trace(stages=stages, events=events)


if __name__ == "__main__":
    import sys

    goal = " ".join(sys.argv[1:]).strip()
    response, trace = run(goal)
    print(response)
    print("TRACE:", " -> ".join(trace.stages))
