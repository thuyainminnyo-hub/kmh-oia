import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "contracts" / "phase-02-8-semantic-context-matrix.json"


class Phase028SemanticContextContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads(CONTRACT.read_text(encoding="utf-8"))

    def test_matrix_has_twelve_unique_required_cases(self):
        cases = self.data["context_fidelity_matrix"]
        self.assertEqual(len(cases), 12)
        ids = [case["id"] for case in cases]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertTrue(all(case["severity"] == "REQUIRED" for case in cases))

    def test_python_fix_is_not_claimed_by_jvm_release_note(self):
        upstream = self.data["upstream"]
        self.assertIn("JVM Java/Kotlin cross-file imports", upstream["verified_scope"])
        self.assertIn("Python cross-file canonical type resolution fixed", upstream["explicitly_not_claimed"])
        self.assertIn("Python cross-file inheritance fixed", upstream["explicitly_not_claimed"])

    def test_same_line_parameter_return_does_not_claim_two_contexts(self):
        case = next(x for x in self.data["context_fidelity_matrix"] if x["id"] == "CTX-03")
        self.assertEqual(case["expected_ast_contexts"], ["parameter_type", "return_type"])
        self.assertIn("insufficient", case["policy"])

    def test_ambiguous_bindings_fail_closed(self):
        for case_id in ("CTX-11", "CTX-12"):
            case = next(x for x in self.data["context_fidelity_matrix"] if x["id"] == case_id)
            self.assertTrue(any(word in case["required_edge"] for word in ("no guessed", "fail closed")))

    def test_governance_keeps_extraction_and_promotion_disabled(self):
        policy = self.data["policy"]
        self.assertEqual(policy["extraction_in_phase"], "NOT_AUTHORIZED")
        self.assertEqual(policy["graphify_execution_count"], 0)
        self.assertFalse(policy["raw_graph_mutation"])
        self.assertFalse(policy["candidate_graph_mutation"])
        self.assertFalse(policy["inferred_or_ambiguous_promotion"])
        self.assertEqual(policy["g4_owner_hold"], "PRESERVED")
        self.assertEqual(policy["production_promotion"], "NOT_AUTHORIZED")

    def test_acceptance_requires_canonical_source_provenance(self):
        acceptance = self.data["acceptance"]
        self.assertTrue(acceptance["canonical_target_must_match_source_file_and_definition_line"])
        self.assertTrue(acceptance["no_name_only_resolution_when_multiple_candidates_exist"])
        self.assertTrue(acceptance["candidate_only_extracted_edges"])
        self.assertTrue(acceptance["raw_graph_immutable"])


if __name__ == "__main__":
    unittest.main()
