"""Minimal executable KMH OIA text-path runtime."""

from dataclasses import dataclass


@dataclass
class Trace:
    stages: list[str]


def run(goal: str) -> tuple[str, Trace]:
    if not goal.strip():
        raise ValueError("goal must not be empty")

    trace = Trace(stages=[])

    trace.stages.append("input_gateway")
    trace.stages.append("oia_core")
    context = {"goal": goal.strip()}
    trace.stages.append("context_assembly")
    trace.stages.append("workflow")
    trace.stages.append("agent")

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
