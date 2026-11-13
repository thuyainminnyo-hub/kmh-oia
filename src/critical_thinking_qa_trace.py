"""Trace integration for the deterministic Critical Thinking QA adapter.

This bridge records a QA verdict in the existing OIA trace contract. It does not
invoke an LLM, run agents, or imply production approval.
"""
from datetime import datetime, timezone

from src.critical_thinking_qa import CriticalThinkingCase, CriticalThinkingQAResult, evaluate_case
from src.trace import ExecutionContext, TraceEvent, Tracer


def evaluate_and_trace(
    case: CriticalThinkingCase,
    tracer: Tracer,
    execution: ExecutionContext,
) -> tuple[CriticalThinkingQAResult, TraceEvent]:
    """Evaluate one case and emit a trace event with shared execution IDs."""
    result = evaluate_case(case)
    status = "ok" if result.verdict == "PASS" else "validation"
    event = TraceEvent(
        stage="critical_thinking_qa",
        status=status,
        metadata={
            "request_id": execution.request_id,
            "session_id": execution.session_id,
            "workflow_id": execution.workflow_id,
            "task_id": execution.task_id,
            "agent_id": execution.agent_id,
            "trace_id": execution.trace_id,
            "correlation_id": result.correlation_id,
            "workflow_version": "KMH-WF-CRIT-QA-001@1.0",
            "input_reference": "inline:structured-case",
            "output_claim": result.original_claim,
            "verdict": result.verdict,
            "checks": "|".join(result.checks),
            "reason": result.reason,
            "execution_status": status,
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        },
    )
    tracer.emit(event)
    return result, event
