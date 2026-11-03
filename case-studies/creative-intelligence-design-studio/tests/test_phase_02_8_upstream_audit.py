import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "contracts" / "phase-02-8-upstream-python-audit.json"


class Phase028UpstreamPythonAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads(AUDIT.read_text(encoding="utf-8"))

    def test_pinned_python_fix_commit_is_in_audited_release_ancestry(self):
        upstream = self.data["upstream"]
        self.assertEqual(upstream["version"], "0.9.100")
        self.assertEqual(upstream["pinned_commit"], "f5155badddaa3286c78a51653791131e9e2e4d29")
        self.assertEqual(upstream["python_type_fix_commit"], "b2825e05a5655be1187250a6acb69b83027acd8a")
        self.assertTrue(upstream["ancestry_verification"]["fix_commit_is_ancestor_of_pinned_commit"])

    def test_python_fix_repoints_all_required_semantic_relations(self):
        relations = set(self.data["upstream"]["key_relations_repointed"])
        self.assertTrue({"references", "inherits", "implements", "extends"} <= relations)

    def test_upstream_regression_inventory_is_complete_and_unique(self):
        tests = self.data["regression_coverage"]
        self.assertEqual(len(tests), 12)
        ids = [item["id"] for item in tests]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertIn("DIRECT_NEGATIVE_TEST", {item["coverage"] for item in tests})
        self.assertTrue(any(item["coverage"] == "EXPLICIT_LIMIT" for item in tests))

    def test_known_context_and_multiple_inheritance_gaps_remain_visible(self):
        gaps = {item["id"]: item for item in self.data["remaining_gaps"]}
        self.assertEqual(len(gaps), 4)
        self.assertIn("same imported symbol", gaps["GAP-01"]["case"])
        self.assertIn("multiple inheritance", gaps["GAP-02"]["case"])
        self.assertEqual(gaps["GAP-04"]["status"], "NOT_REPRODUCED")

    def test_open_issue_status_does_not_override_pinned_commit_evidence(self):
        issues = {item["number"]: item for item in self.data["issues"]}
        self.assertEqual(issues[1186]["state_observed"], "OPEN")
        self.assertEqual(issues[3252]["state_observed"], "OPEN")
        self.assertIn("included in v0.9.100", issues[3252]["classification"])
        self.assertEqual(issues[4262]["state_observed"], "CLOSED")

    def test_no_extraction_or_governance_promotion_is_authorized(self):
        governance = self.data["governance"]
        self.assertEqual(governance["graphify_execution_count_in_phase_02_8"], 0)
        self.assertFalse(governance["new_extraction_authorized"])
        self.assertFalse(governance["raw_graph_mutation"])
        self.assertFalse(governance["candidate_graph_mutation"])
        self.assertFalse(governance["inferred_or_ambiguous_promotion"])
        self.assertEqual(governance["g4_owner_hold"], "PRESERVED")
        self.assertEqual(governance["production_promotion"], "NOT_AUTHORIZED")


if __name__ == "__main__":
    unittest.main()
