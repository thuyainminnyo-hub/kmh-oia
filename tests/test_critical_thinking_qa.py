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
        self.assertEqual(result.verdict, "REWORK")
        self.assertIn("revised_conclusion_text:missing_or_unchanged", result.checks)

    def test_unchanged_revised_universal_claim_returns_rework(self):
        claim = "Nobody at the university speaks French."
        result = evaluate_case(CriticalThinkingCase(
            correlation_id="KMH-CRITQA-TEST-006",
            original_claim=claim,
            evidence_count=2,
            conclusion_scope="universal",
            conclusion_qualified=True,
            revised_conclusion=claim,
        ))
        self.assertEqual(result.verdict, "REWORK")
        self.assertEqual(result.original_claim, claim)

    def test_revised_conclusion_requires_human_semantic_review(self):
        claim = "Nobody at the university speaks French."
        result = evaluate_case(CriticalThinkingCase(
            correlation_id="KMH-CRITQA-TEST-007",
            original_claim=claim,
            evidence_count=2,
            conclusion_scope="universal",
            conclusion_qualified=True,
            revised_conclusion="The two people observed do not speak French.",
        ))
        self.assertEqual(result.verdict, "HUMAN_REVIEW")
        self.assertEqual(result.original_claim, claim)
        self.assertIn("revised_conclusion_semantics:human_review_required", result.checks)

    def test_unqualified_universal_claim_returns_rework(self):
        result = evaluate_case(CriticalThinkingCase(
            correlation_id="KMH-CRITQA-TEST-002",
            original_claim="Nobody at the university speaks French.",
            evidence_count=2,
            conclusion_scope="universal",
        ))
        self.assertEqual(result.verdict, "REWORK")
        self.assertIn("revised_conclusion_text:missing_or_unchanged", result.checks)

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

    def test_unrecognized_scope_fails_closed(self):
        result = evaluate_case(CriticalThinkingCase(
            correlation_id="KMH-CRITQA-TEST-008",
            original_claim="A claim.",
            evidence_count=1,
            conclusion_scope="apparently_bounded",  # type: ignore[arg-type]
        ))
        self.assertEqual(result.verdict, "REWORK")
        self.assertIn("input_schema:fail", result.checks)

    def test_boolean_evidence_count_fails_closed(self):
        result = evaluate_case(CriticalThinkingCase(
            correlation_id="KMH-CRITQA-TEST-009",
            original_claim="A claim.",
            evidence_count=True,  # type: ignore[arg-type]
            conclusion_scope="bounded",
        ))
        self.assertEqual(result.verdict, "REWORK")
        self.assertIn("input_schema:fail", result.checks)

    def test_negative_evidence_count_fails_closed(self):
        result = evaluate_case(CriticalThinkingCase(
            correlation_id="KMH-CRITQA-TEST-010",
            original_claim="A claim.",
            evidence_count=-1,
            conclusion_scope="bounded",
        ))
        self.assertEqual(result.verdict, "REWORK")
        self.assertIn("input_schema:fail", result.checks)

    def test_non_string_claim_fails_closed_without_crashing(self):
        result = evaluate_case(CriticalThinkingCase(
            correlation_id="KMH-CRITQA-TEST-011",
            original_claim=None,  # type: ignore[arg-type]
            evidence_count=1,
            conclusion_scope="bounded",
        ))
        self.assertEqual(result.verdict, "REWORK")
        self.assertEqual(result.original_claim, "")
        self.assertIn("input_schema:fail", result.checks)

    def test_zero_evidence_cannot_pass_even_if_population_flag_is_true(self):
        result = evaluate_case(CriticalThinkingCase(
            correlation_id="KMH-CRITQA-TEST-012",
            original_claim="Every item in the population has property X.",
            evidence_count=0,
            conclusion_scope="universal",
            evidence_covers_entire_population=True,
        ))
        self.assertEqual(result.verdict, "REWORK")
        self.assertIn("evidence_count:fail", result.checks)


if __name__ == "__main__":
    unittest.main()
