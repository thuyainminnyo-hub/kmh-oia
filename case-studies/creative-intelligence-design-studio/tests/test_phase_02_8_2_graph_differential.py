import copy
import tempfile
import unittest
from pathlib import Path

from scripts.validate_phase_02_7_graph import validate_graph


class Phase0282SyntheticGraphDifferentialTests(unittest.TestCase):
    """Validate synthetic graph records against source-derived AST expectations.

    The graph below is deliberately constructed test input, not Graphify output.
    These tests verify the KMH validation contract and its fail-closed behavior.
    """

    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)

        files = {
            ".graphifyignore": "**/.env\n",
            "src/pkg_a/__init__.py": "",
            "src/pkg_a/types.py": (
                "class Widget:\n"
                "    pass\n"
                "\n"
                "class BaseA:\n"
                "    pass\n"
            ),
            "src/pkg_b/__init__.py": "",
            "src/pkg_b/types.py": (
                "class Widget:\n"
                "    pass\n"
                "\n"
                "class BaseB:\n"
                "    pass\n"
            ),
            "src/consumer.py": (
                "from pkg_a.types import Widget as AWidget, BaseA\n"
                "from pkg_b.types import Widget as BWidget, BaseB\n"
                "\n"
                "def accept_a(value: AWidget) -> AWidget:\n"
                "    return value\n"
                "\n"
                "def accept_b(value: BWidget) -> BWidget:\n"
                "    return value\n"
                "\n"
                "class Combined(BaseA, BaseB):\n"
                "    pass\n"
            ),
        }
        for relative, text in files.items():
            path = self.root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")

        self.source_files = sorted(path for path in files if path.endswith(".py"))
        self.baseline = {
            "baseline_id": "KMH-PHASE-02.8.2-SYNTHETIC-DIFFERENTIAL-v1",
            "source_files": self.source_files,
            "coverage_matrix": [
                {
                    "name": "alpha-same-name-widget-parameter",
                    "importer_file": "src/consumer.py",
                    "imported_name": "Widget",
                    "target_file": "src/pkg_a/types.py",
                    "category": "TYPE_ANNOTATION",
                    "relation": "references",
                },
                {
                    "name": "beta-same-name-widget-parameter",
                    "importer_file": "src/consumer.py",
                    "imported_name": "Widget",
                    "target_file": "src/pkg_b/types.py",
                    "category": "TYPE_ANNOTATION",
                    "relation": "references",
                },
                {
                    "name": "alpha-multiple-inheritance-base",
                    "importer_file": "src/consumer.py",
                    "imported_name": "BaseA",
                    "target_file": "src/pkg_a/types.py",
                    "category": "CLASS_BASE",
                    "relation": "inherits",
                },
                {
                    "name": "beta-multiple-inheritance-base",
                    "importer_file": "src/consumer.py",
                    "imported_name": "BaseB",
                    "target_file": "src/pkg_b/types.py",
                    "category": "CLASS_BASE",
                    "relation": "inherits",
                },
            ],
        }
        self.raw = {
            "nodes": [
                {"id": "pkg_a_widget", "label": "Widget", "file_type": "code", "source_file": "src/pkg_a/types.py", "source_location": "L1"},
                {"id": "pkg_a_basea", "label": "BaseA", "file_type": "code", "source_file": "src/pkg_a/types.py", "source_location": "L4"},
                {"id": "pkg_b_widget", "label": "Widget", "file_type": "code", "source_file": "src/pkg_b/types.py", "source_location": "L1"},
                {"id": "pkg_b_baseb", "label": "BaseB", "file_type": "code", "source_file": "src/pkg_b/types.py", "source_location": "L4"},
                {"id": "consumer_accept_a", "label": "accept_a()", "file_type": "code", "source_file": "src/consumer.py", "source_location": "L4"},
                {"id": "consumer_accept_b", "label": "accept_b()", "file_type": "code", "source_file": "src/consumer.py", "source_location": "L7"},
                {"id": "consumer_combined", "label": "Combined", "file_type": "code", "source_file": "src/consumer.py", "source_location": "L10"},
            ],
            "edges": [
                {"source": "consumer_accept_a", "target": "pkg_a_widget", "relation": "references", "context": "parameter_type", "confidence": "EXTRACTED", "source_file": "src/consumer.py", "source_location": "L4"},
                {"source": "consumer_accept_b", "target": "pkg_b_widget", "relation": "references", "context": "parameter_type", "confidence": "EXTRACTED", "source_file": "src/consumer.py", "source_location": "L7"},
                {"source": "consumer_combined", "target": "pkg_a_basea", "relation": "inherits", "confidence": "EXTRACTED", "source_file": "src/consumer.py", "source_location": "L10"},
                {"source": "consumer_combined", "target": "pkg_b_baseb", "relation": "inherits", "confidence": "EXTRACTED", "source_file": "src/consumer.py", "source_location": "L10"},
                {"source": "consumer_accept_a", "target": "pkg_a_widget", "relation": "uses", "confidence": "INFERRED", "confidence_score": 0.95, "source_file": "src/consumer.py", "source_location": "L4"},
            ],
        }

    def run_validation(self, raw=None):
        return validate_graph(copy.deepcopy(raw if raw is not None else self.raw), self.root, self.baseline)

    def test_same_named_imports_bind_to_distinct_package_definitions(self):
        report, candidate = self.run_validation()
        self.assertEqual(report["status"], "PASS_WITH_WARNINGS", report["errors"])
        targets = {
            (item["local_name"], item["target_file"], item["target_node_id"])
            for item in report["canonical_semantic_links"]
            if item["relation"] == "references"
        }
        self.assertIn(("AWidget", "src/pkg_a/types.py", "pkg_a_widget"), targets)
        self.assertIn(("BWidget", "src/pkg_b/types.py", "pkg_b_widget"), targets)
        self.assertEqual(
            len(report["same_named_definition_groups"]["Widget"]), 2
        )

    def test_same_line_parameter_and_return_is_warning_not_false_return_pass(self):
        report, _ = self.run_validation()
        warnings = [
            warning for warning in report["warnings"]
            if isinstance(warning, dict)
            and warning.get("code") == "SIGNATURE_ANNOTATION_EDGE_COALESCED"
        ]
        self.assertEqual(len(warnings), 2)
        self.assertEqual(report["semantic_context_fidelity"], "PARTIAL_WITH_WARNINGS")
        return_links = [
            item for item in report["canonical_semantic_links"]
            if item["context"] == "return_type"
        ]
        self.assertEqual(len(return_links), 2)
        self.assertTrue(all(item["context_match_mode"] == "coalesced_signature_annotation" for item in return_links))

    def test_multiple_inheritance_requires_each_canonical_base_edge(self):
        report, _ = self.run_validation()
        bases = [
            item for item in report["canonical_semantic_links"]
            if item["relation"] == "inherits"
        ]
        self.assertEqual(
            {(item["imported_name"], item["target_file"]) for item in bases},
            {("BaseA", "src/pkg_a/types.py"), ("BaseB", "src/pkg_b/types.py")},
        )
        self.assertTrue(all(item["raw_extracted_edge_matches"] == 1 for item in bases))

    def test_wrong_same_name_package_target_fails_closed(self):
        raw = copy.deepcopy(self.raw)
        raw["edges"][0]["target"] = "pkg_b_widget"
        report, _ = self.run_validation(raw)
        self.assertEqual(report["status"], "FAIL")
        self.assertTrue(any(
            isinstance(error, dict)
            and error.get("code") == "CANONICAL_SEMANTIC_EDGE_NOT_UNIQUE"
            and error.get("imported_name") == "Widget"
            and error.get("target_file") == "src/pkg_a/types.py"
            for error in report["errors"]
        ))

    def test_missing_second_inheritance_edge_fails(self):
        raw = copy.deepcopy(self.raw)
        raw["edges"] = [
            edge for edge in raw["edges"]
            if not (edge["relation"] == "inherits" and edge["target"] == "pkg_b_baseb")
        ]
        report, _ = self.run_validation(raw)
        self.assertEqual(report["status"], "FAIL")
        self.assertTrue(any(
            isinstance(error, dict)
            and error.get("code") == "CANONICAL_SEMANTIC_EDGE_NOT_UNIQUE"
            and error.get("relation") == "inherits"
            and error.get("target_label") == "BaseB"
            for error in report["errors"]
        ))

    def test_edge_with_wrong_source_provenance_does_not_match(self):
        raw = copy.deepcopy(self.raw)
        raw["edges"][0]["source_file"] = "src/pkg_a/types.py"
        report, _ = self.run_validation(raw)
        self.assertEqual(report["status"], "FAIL")
        self.assertTrue(any(
            isinstance(error, dict)
            and error.get("code") == "CANONICAL_SEMANTIC_EDGE_NOT_UNIQUE"
            for error in report["errors"]
        ))

    def test_inferred_edge_stays_out_of_candidate_and_raw_is_immutable(self):
        before = copy.deepcopy(self.raw)
        report, candidate = self.run_validation()
        self.assertEqual(self.raw, before)
        self.assertEqual(
            len(candidate["edges"]),
            sum(1 for edge in self.raw["edges"] if edge["confidence"] == "EXTRACTED"),
        )
        self.assertFalse(any(edge["confidence"] != "EXTRACTED" for edge in candidate["edges"]))
        self.assertEqual(report["raw_graph"]["edge_count"], 5)
        self.assertEqual(report["candidate_graph"]["edge_count"], 4)
        self.assertFalse(report["governance"]["raw_graph_mutated"])

    def test_duplicate_declaration_in_imported_module_fails_closed(self):
        path = self.root / "src/pkg_a/types.py"
        path.write_text(
            "class Widget:\n    pass\n\nclass Widget:\n    pass\n\nclass BaseA:\n    pass\n",
            encoding="utf-8",
        )
        report, _ = self.run_validation()
        self.assertEqual(report["status"], "FAIL")
        self.assertTrue(any(
            isinstance(error, dict)
            and error.get("code") == "INTERNAL_IMPORT_NOT_UNIQUE"
            for error in report["errors"]
        ))

    def test_star_import_is_rejected_as_unresolved_not_guessed(self):
        path = self.root / "src/consumer.py"
        path.write_text("from pkg_a.types import *\n", encoding="utf-8")
        report, _ = self.run_validation()
        self.assertEqual(report["status"], "FAIL")
        self.assertTrue(any(
            isinstance(error, dict)
            and error.get("code") == "STAR_IMPORT_NOT_ALLOWED"
            for error in report["errors"]
        ))


if __name__ == "__main__":
    unittest.main()
