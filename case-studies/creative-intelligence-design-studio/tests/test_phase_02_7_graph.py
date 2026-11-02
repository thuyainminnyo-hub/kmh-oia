import copy
import json
import tempfile
import unittest
from pathlib import Path

from scripts.validate_phase_02_7_graph import validate_graph


class Phase027GraphValidationTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        (self.root / "src/pkg").mkdir(parents=True)
        (self.root / ".graphifyignore").write_text("**/.env\n", encoding="utf-8")
        (self.root / "src/pkg/__init__.py").write_text('"""Package."""\n', encoding="utf-8")
        self.models = "class Widget:\n    pass\n"
        self.service = (
            "from .models import Widget as W\n\n"
            "def build(value: W) -> W:\n"
            "    return W()\n"
        )
        (self.root / "src/pkg/models.py").write_text(self.models, encoding="utf-8")
        (self.root / "src/pkg/service.py").write_text(self.service, encoding="utf-8")
        self.source_files = ["src/pkg/__init__.py", "src/pkg/models.py", "src/pkg/service.py"]
        self.baseline = {
            "baseline_id": "TEST-PHASE-02.7",
            "source_files": self.source_files,
            "coverage_matrix": [
                {"importer_file": "src/pkg/service.py", "imported_name": "Widget", "target_file": "src/pkg/models.py", "category": "TYPE_ANNOTATION", "relation": "references"},
                {"importer_file": "src/pkg/service.py", "imported_name": "Widget", "target_file": "src/pkg/models.py", "category": "RUNTIME_CALL", "relation": "calls"},
            ],
        }
        self.raw = {
            "nodes": [
                {"id": "pkg_widget", "label": "Widget", "file_type": "code", "source_file": "src/pkg/models.py", "source_location": "L1"},
                {"id": "pkg_build", "label": "build()", "file_type": "code", "source_file": "src/pkg/service.py", "source_location": "L3"},
                {"id": "pkg_file", "label": "service.py", "file_type": "code", "source_file": "src/pkg/service.py", "source_location": "L1"},
                {"id": "models_file", "label": "models.py", "file_type": "code", "source_file": "src/pkg/models.py", "source_location": "L1"},
            ],
            "edges": [
                {"source": "pkg_build", "target": "pkg_widget", "relation": "references", "context": "parameter_type", "confidence": "EXTRACTED", "source_file": "src/pkg/service.py", "source_location": "L3"},
                {"source": "pkg_build", "target": "pkg_widget", "relation": "references", "context": "return_type", "confidence": "EXTRACTED", "source_file": "src/pkg/service.py", "source_location": "L3"},
                {"source": "pkg_build", "target": "pkg_widget", "relation": "calls", "context": "call", "confidence": "EXTRACTED", "source_file": "src/pkg/service.py", "source_location": "L4"},
                {"source": "pkg_build", "target": "pkg_widget", "relation": "uses", "confidence": "INFERRED", "source_file": "src/pkg/service.py", "source_location": "L3"},
            ],
        }
        
    def test_valid_alias_relative_import_and_extracted_candidate(self):
        result, candidate = validate_graph(copy.deepcopy(self.raw), self.root, self.baseline)
        self.assertEqual(result["status"], "PASS", result["errors"])
        self.assertEqual(len(result["canonical_semantic_links"]), 3)
        self.assertEqual(len(candidate["edges"]), 3)
        self.assertFalse(any(e["confidence"] != "EXTRACTED" for e in candidate["edges"]))
        self.assertEqual(result["candidate_graph"]["edge_count"], 3)

    def test_wrong_cross_file_target_fails(self):
        raw = copy.deepcopy(self.raw)
        raw["edges"][0]["target"] = "ghost_widget"
        result, _ = validate_graph(raw, self.root, self.baseline)
        self.assertEqual(result["status"], "FAIL")
        self.assertTrue(any(e.get("code") == "CANONICAL_SEMANTIC_EDGE_NOT_UNIQUE" for e in result["errors"]))

    def test_dangling_endpoint_fails(self):
        raw = copy.deepcopy(self.raw)
        raw["edges"][0]["target"] = "missing-node"
        result, _ = validate_graph(raw, self.root, self.baseline)
        self.assertEqual(result["status"], "FAIL")
        self.assertTrue(any("target endpoint is unresolved" in e for e in result["errors"]))

    def test_same_label_duplicate_definitions_have_separate_canonical_ids(self):
        result, _ = validate_graph(copy.deepcopy(self.raw), self.root, self.baseline)
        self.assertEqual(result["status"], "PASS", result["errors"])
        self.assertEqual(result["same_named_definition_groups"], {})

    def test_unapproved_file_in_snapshot_fails(self):
        (self.root / "src/pkg/secret.py").write_text("password = 'no'\n", encoding="utf-8")
        result, _ = validate_graph(copy.deepcopy(self.raw), self.root, self.baseline)
        self.assertEqual(result["status"], "FAIL")
        self.assertTrue(any("scan snapshot file set differs" in e for e in result["errors"]))

    def test_candidate_preserves_raw_nodes_and_excludes_review_edges(self):
        before = copy.deepcopy(self.raw)
        result, candidate = validate_graph(self.raw, self.root, self.baseline)
        self.assertEqual(self.raw, before)
        self.assertEqual(candidate["nodes"], self.raw["nodes"])
        self.assertEqual(len(candidate["edges"]), 3)
        self.assertEqual(result["raw_graph"]["edge_count"], 4)


if __name__ == "__main__":
    unittest.main()
