import unittest

from src.critical_thinking_qa import CriticalThinkingCase
from src.critical_thinking_qa_trace import evaluate_and_trace
from src.trace import ExecutionContext, InMemoryTracer


class CriticalThinkingQATraceTests(unittest.TestCase):
    def test_qa_verdict_is_traced_with_correlation_and_execution_ids(self):
        execution = ExecutionContext.create("qa-session-1")
        tracer = InMemoryTracer()
        case = CriticalThinkingCase(
            correlation_id="KMH-CRITQA-TRACE-001",
            original_claim="The two observed people do not speak French.",
            evidence_count=2,
            conclusion_scope="bounded",
        )

        result, event = evaluate_and_trace(case, tracer, execution)

        self.assertEqual(result.verdict, "PASS")
        self.assertEqual(len(tracer.events), 1)
        self.assertIs(tracer.events[0], event)
        self.assertEqual(event.stage, "critical_thinking_qa")
        self.assertEqual(event.metadata["correlation_id"], "KMH-CRITQA-TRACE-001")
        self.assertEqual(event.metadata["verdict"], "PASS")
        for key in InMemoryTracer.REQUIRED_CONTEXT_KEYS:
            self.assertEqual(event.metadata[key], getattr(execution, key))
        tracer.validate_integrity()

    def test_rework_verdict_is_traced_as_validation_not_pass(self):
        execution = ExecutionContext.create("qa-session-2")
        tracer = InMemoryTracer()
        case = CriticalThinkingCase(
            correlation_id="KMH-CRITQA-TRACE-002",
            original_claim="Nobody at the university speaks French.",
            evidence_count=2,
            conclusion_scope="universal",
        )

        result, event = evaluate_and_trace(case, tracer, execution)

        self.assertEqual(result.verdict, "REWORK")
        self.assertEqual(event.status, "validation")
        self.assertEqual(event.metadata["verdict"], "REWORK")
        tracer.validate_integrity()

    def test_human_review_verdict_remains_explicit_in_trace(self):
        execution = ExecutionContext.create("qa-session-3")
        tracer = InMemoryTracer()
        case = CriticalThinkingCase(
            correlation_id="KMH-CRITQA-TRACE-003",
            original_claim="Nobody at the university speaks French.",
            evidence_count=2,
            conclusion_scope="universal",
            revised_conclusion="The two observed people do not speak French.",
        )

        result, event = evaluate_and_trace(case, tracer, execution)

        self.assertEqual(result.verdict, "HUMAN_REVIEW")
        self.assertEqual(event.status, "validation")
        self.assertIn("revised_conclusion_semantics:human_review_required", event.metadata["checks"])
        tracer.validate_integrity()


if __name__ == "__main__":
    unittest.main()
