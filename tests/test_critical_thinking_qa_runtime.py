import unittest

from src.critical_thinking_qa import CriticalThinkingCase
from src.critical_thinking_qa_runtime import CriticalThinkingQARuntime
from src.trace import ExecutionContext, InMemoryTracer


class CriticalThinkingQARuntimeTests(unittest.TestCase):
    def test_pass_uses_supplied_execution_context_and_emits_ok(self) -> None:
        tracer = InMemoryTracer()
        execution = ExecutionContext(
            request_id="req-1",
            session_id="session-1",
            workflow_id="workflow-1",
            task_id="task-1",
            agent_id="agent-1",
            trace_id="trace-1",
        )
        case = CriticalThinkingCase(
            correlation_id="corr-1",
            original_claim="This sample contains five records.",
            evidence_count=5,
            conclusion_scope="bounded",
        )

        result = CriticalThinkingQARuntime(tracer).review(case, execution=execution)

        self.assertEqual(result.qa.verdict, "PASS")
        self.assertEqual(result.event.stage, "critical_thinking_qa")
        self.assertEqual(result.event.status, "ok")
        self.assertEqual(result.execution, execution)
        for key in (
            "request_id", "session_id", "workflow_id",
            "task_id", "agent_id", "trace_id",
        ):
            self.assertEqual(result.event.metadata[key], getattr(execution, key))
        self.assertEqual(result.event.metadata["correlation_id"], "corr-1")
        tracer.validate_integrity()

    def test_rework_fails_closed_as_validation_event(self) -> None:
        tracer = InMemoryTracer()
        case = CriticalThinkingCase(
            correlation_id="corr-2",
            original_claim="All cases behave this way.",
            evidence_count=2,
            conclusion_scope="universal",
            evidence_covers_entire_population=False,
        )

        result = CriticalThinkingQARuntime(tracer).review(case)

        self.assertEqual(result.qa.verdict, "REWORK")
        self.assertEqual(result.event.status, "validation")
        self.assertNotEqual(result.event.status, "ok")
        self.assertEqual(len(tracer.events), 1)
        tracer.validate_integrity()

    def test_human_review_is_validation_event(self) -> None:
        tracer = InMemoryTracer()
        case = CriticalThinkingCase(
            correlation_id="corr-3",
            original_claim="All cases behave this way.",
            evidence_count=2,
            conclusion_scope="universal",
            revised_conclusion="In this small sample, these cases behaved this way.",
        )

        result = CriticalThinkingQARuntime(tracer).review(case, session_id="review-session")

        self.assertEqual(result.qa.verdict, "HUMAN_REVIEW")
        self.assertEqual(result.event.status, "validation")
        self.assertEqual(result.execution.session_id, "review-session")
        tracer.validate_integrity()

    def test_rejects_free_text_instead_of_structured_case(self) -> None:
        runtime = CriticalThinkingQARuntime(InMemoryTracer())

        with self.assertRaisesRegex(TypeError, "CriticalThinkingCase"):
            runtime.review("All claims are correct.")  # type: ignore[arg-type]

    def test_rejects_ambiguous_execution_and_session_id(self) -> None:
        runtime = CriticalThinkingQARuntime(InMemoryTracer())
        case = CriticalThinkingCase(
            correlation_id="corr-4",
            original_claim="A bounded claim.",
            evidence_count=1,
            conclusion_scope="bounded",
        )
        execution = ExecutionContext.create("existing-session")

        with self.assertRaisesRegex(ValueError, "not both"):
            runtime.review(case, execution=execution, session_id="other-session")


if __name__ == "__main__":
    unittest.main()
