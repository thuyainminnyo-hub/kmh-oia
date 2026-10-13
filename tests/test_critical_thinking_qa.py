import unittest

from src.critical_thinking_qa import CriticalThinkingCase, evaluate_case


class CriticalThinkingQATests(unittest.TestCase):
    def test_preserves_original_claim_and_correlation_id(self):
        claim = "Two people do not speak French; therefore nobody does."
        result = evaluate_case(CriticalThinkingCase(
            correlation_id="KMH-CRITQA-TEST-001",
            original_claim=claim,
            evidence_count=2,
            conclusion_scope="universal",
            conclusion_qualified=True,
        ))
        self.assertEqual(result.original_claim, claim)
        self.assertEqual(result.correlation_id, "KMH-CRITQA-TEST-001")
        self.assertEqual(result.verdict, "PASS")

    def test_unqualified_universal_claim_returns_rework(self):
        result = evaluate_case(CriticalThinkingCase(
            correlation_id="KMH-CRITQA-TEST-002",
            original_claim="Nobody at the university speaks French.",
            evidence_count=2,
            conclusion_scope="universal",
        ))
        self.assertEqual(result.verdict, "REWORK")
        self.assertIn("uncertainty_qualification:fail", result.checks)

    def test_explicit_human_review_gate_wins(self):
        result = evaluate_case(CriticalThinkingCase(
            correlation_id="KMH-CRITQA-TEST-003",
            original_claim="The evidence is ambiguous.",
            evidence_count=1,
            conclusion_scope="bounded",
            human_review_required=True,
        ))
        self.assertEqual(result.verdict, "HUMAN_REVIEW")

    def test_unknown_scope_requires_human_review(self):
        result = evaluate_case(CriticalThinkingCase(
            correlation_id="KMH-CRITQA-TEST-004",
            original_claim="It might be true.",
            evidence_count=1,
            conclusion_scope="unknown",
        ))
        self.assertEqual(result.verdict, "HUMAN_REVIEW")

    def test_invalid_input_returns_rework(self):
        result = evaluate_case(CriticalThinkingCase(
            correlation_id=" ",
            original_claim="Claim",
            evidence_count=1,
            conclusion_scope="bounded",
        ))
        self.assertEqual(result.verdict, "REWORK")


if __name__ == "__main__":
    unittest.main()
