"""Explicit runtime entry point for structured Critical Thinking QA cases.

This module only accepts a CriticalThinkingCase object; it never infers QA
metadata from a runtime goal or arbitrary user text. Non-PASS outcomes remain
validation events and must not be treated as successful QA.
"""
from dataclasses import dataclass

from src.critical_thinking_qa import CriticalThinkingCase, CriticalThinkingQAResult
from src.critical_thinking_qa_trace import evaluate_and_trace
from src.trace import ExecutionContext, InMemoryTracer, TraceEvent, Tracer


@dataclass(frozen=True)
class CriticalThinkingQARuntimeResult:
    """Result and trace evidence for one explicit structured QA invocation."""

    qa: CriticalThinkingQAResult
    event: TraceEvent
    execution: ExecutionContext


class CriticalThinkingQARuntime:
    """Run deterministic QA through an explicit, traceable runtime boundary."""

    def __init__(self, tracer: Tracer | None = None) -> None:
        self.tracer = tracer or InMemoryTracer()

    def review(
        self,
        case: CriticalThinkingCase,
        *,
        execution: ExecutionContext | None = None,
        session_id: str | None = None,
    ) -> CriticalThinkingQARuntimeResult:
        """Evaluate a structured case and emit a trace event.

        Callers may supply an existing ExecutionContext to preserve IDs across
        runtime stages. Otherwise a context is created for this QA invocation.
        A non-PASS verdict is emitted with status='validation', never 'ok'.
        """
        if not isinstance(case, CriticalThinkingCase):
            raise TypeError(
                "case must be a CriticalThinkingCase; free-text inference is unsupported"
            )
        if execution is not None and session_id is not None:
            raise ValueError("provide execution or session_id, not both")
        context = execution or ExecutionContext.create(
            session_id=session_id or f"critical-thinking-qa:{case.correlation_id}"
        )
        qa_result, event = evaluate_and_trace(case, self.tracer, context)
        if qa_result.verdict != "PASS" and event.status == "ok":
            # Defensive invariant: fail closed if the trace adapter ever drifts.
            raise RuntimeError("non-PASS QA verdict cannot emit an ok trace event")
        if qa_result.verdict == "PASS" and event.status != "ok":
            raise RuntimeError("PASS QA verdict must emit an ok trace event")
        return CriticalThinkingQARuntimeResult(
            qa=qa_result, event=event, execution=context
        )
