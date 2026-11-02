import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from scripts.validate_canonical_semantics import validate


class CanonicalSemanticValidationTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        (self.root / "src").mkdir()
        self.flow = (
            '"""Synthetic consumer fixture."""\n\n'
            "from contract_guard import DesignToken as Token, is_approved_token\n\n"
            "def select_outfit(token: Token):\n"
            "    if not is_approved_token(token):\n"
            "        raise ValueError('not approved')\n"
            "    return token.token_name\n\n"
            "class OutfitChild(Token):\n"
            "    pass\n"
        )
        self.guard = (
            '"""Synthetic contract fixture."""\n\n'
            "from dataclasses import dataclass\n\n"
            "@dataclass(frozen=True)\n"
            "class DesignToken:\n"
            "    token_name: str\n"
            "    approved: bool\n\n"
            "def is_approved_token(token: DesignToken) -> bool:\n"
            "    return bool(token.token_name.strip()) and token.approved\n"
        )
        (self.root / "src/outfit_flow.py").write_text(self.flow, encoding="utf-8")
        (self.root / "src/contract_guard.py").write_text(self.guard, encoding="utf-8")
        self.nodes = [
            {"id": "src_outfit_flow_select_outfit", "label": "select_outfit()", "file_type": "code", "source_file": "src/outfit_flow.py", "source_location": "L5", "_callable": True},
            {"id": "src_outfit_flow_outfitchild", "label": "OutfitChild", "file_type": "code", "source_file": "src/outfit_flow.py", "source_location": "L10", "_callable": True, "_callable_class": True},
            {"id": "src_contract_guard_designtoken", "label": "DesignToken", "file_type": "code", "source_file": "src/contract_guard.py", "source_location": "L6", "_callable": True, "_callable_class": True},
            {"id": "src_contract_guard_is_approved_token", "label": "is_approved_token()", "file_type": "code", "source_file": "src/contract_guard.py", "source_location": "L10", "_callable": True},
        ]
        self.edges = [
            {"source": "src_outfit_flow_select_outfit", "target": "src_contract_guard_designtoken", "relation": "references", "context": "parameter_type", "confidence": "EXTRACTED", "source_file": "src/outfit_flow.py", "source_location": "L5"},
            {"source": "src_outfit_flow_select_outfit", "target": "src_contract_guard_is_approved_token", "relation": "calls", "context": "call", "confidence": "EXTRACTED", "source_file": "src/outfit_flow.py", "source_location": "L6"},
            {"source": "src_outfit_flow_outfitchild", "target": "src_contract_guard_designtoken", "relation": "inherits", "context": "base", "confidence": "EXTRACTED", "source_file": "src/outfit_flow.py", "source_location": "L10"},
            {"source": "src_outfit_flow_select_outfit", "target": "src_contract_guard_designtoken", "relation": "uses", "confidence": "INFERRED", "confidence_score": 0.95, "source_file": "src/outfit_flow.py", "source_location": "L5"},
        ]
        self.raw = {"nodes": copy.deepcopy(self.nodes), "edges": copy.deepcopy(self.edges), "hyperedges": []}
        self.candidate = {"nodes": copy.deepcopy(self.nodes), "edges": copy.deepcopy(self.edges[:3]), "hyperedges": []}
        held = self.edges[3]
        identity = {k: held.get(k) for k in ("source", "target", "relation", "confidence", "source_file", "source_location")}
        fp = hashlib.sha256(json.dumps(identity, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        self.manifest = {
            "edge_decisions": [{
                "edge_fingerprint": fp,
                "edge_identity": identity,
                "disposition": "HOLD_NOT_PROMOTED",
                "owner_confirmation": "CONFIRMED_HOLD",
            }]
        }
        self.graph_baseline = {
            "graphs": {
                "raw_sha256": "not-used-by-library",
                "candidate_sha256": "not-used-by-library",
            },
            "graphify": {"version": "0.9.100", "source_commit": "f" * 40},
        }
        self.semantic_baseline = {
            "baseline_id": "KMH-CREATIVE-CANONICAL-SEMANTICS-02.6-v1",
            "semantic_expectations": [
                {"source_symbol": "select_outfit()", "imported_name": "DesignToken", "category": "TYPE_ANNOTATION", "relation": "references", "source_file": "src/outfit_flow.py", "source_location": "L5", "target_file": "src/contract_guard.py", "target_symbol": "DesignToken", "target_definition": "L6", "context": "parameter_type"},
                {"source_symbol": "select_outfit()", "imported_name": "is_approved_token", "category": "RUNTIME_CALL", "relation": "calls", "source_file": "src/outfit_flow.py", "source_location": "L6", "target_file": "src/contract_guard.py", "target_symbol": "is_approved_token()", "target_definition": "L10", "context": "call"},
                {"source_symbol": "OutfitChild", "imported_name": "DesignToken", "category": "CLASS_BASE", "relation": "inherits", "source_file": "src/outfit_flow.py", "source_location": "L10", "target_file": "src/contract_guard.py", "target_symbol": "DesignToken", "target_definition": "L6", "context": "base"},
            ],
            "graphify": {"version": "0.9.100", "source_commit": "f" * 40},
            "held_edge": {
                "source_node_id": held["source"],
                "target_node_id": held["target"],
                "source_file": held["source_file"],
                "source_location": held["source_location"],
            },
            "upstream_regression_tests": [
                "tests/test_extract.py::test_cross_file_type_annotation_refs_resolve_to_single_node",
                "tests/test_extract.py::test_3252_inheritance_repoints_inherits_edge",
            ],
        }

    def check(self, raw=None, candidate=None, manifest=None):
        return validate(
            raw or self.raw,
            candidate or self.candidate,
            manifest or self.manifest,
            self.graph_baseline,
            self.semantic_baseline,
            self.root,
        )

    def test_alias_type_annotation_call_and_inheritance_resolve_to_canonical_nodes(self):
        result = self.check()
        self.assertEqual(result["status"], "PASS", result["errors"])
        categories = {item["category"] for item in result["semantic_edges"]}
        self.assertEqual(categories, {"TYPE_ANNOTATION", "RUNTIME_CALL", "CLASS_BASE"})
        self.assertEqual(len(result["canonical_import_targets"]), 2)
        self.assertFalse(result["held_edge"]["candidate_present"])

    def test_wrong_canonical_type_target_fails(self):
        raw = copy.deepcopy(self.raw)
        raw["edges"][0]["target"] = "ghost_design_token"
        result = self.check(raw=raw)
        self.assertEqual(result["status"], "FAIL")
        self.assertTrue(any(e.get("code") == "RAW_SEMANTIC_EDGE_MISSING_OR_DUPLICATED" for e in result["errors"]))

    def test_missing_canonical_target_node_fails(self):
        raw = copy.deepcopy(self.raw)
        raw["nodes"] = [n for n in raw["nodes"] if n["id"] != "src_contract_guard_designtoken"]
        result = self.check(raw=raw)
        self.assertEqual(result["status"], "FAIL")
        self.assertTrue(any(e.get("code") == "CANONICAL_TARGET_NODE_NOT_UNIQUE" for e in result["errors"]))

    def test_duplicate_canonical_target_node_fails(self):
        raw = copy.deepcopy(self.raw)
        raw["nodes"].append(copy.deepcopy(raw["nodes"][2]))
        result = self.check(raw=raw)
        self.assertEqual(result["status"], "FAIL")
        self.assertTrue(any(e.get("code") == "CANONICAL_TARGET_NODE_NOT_UNIQUE" for e in result["errors"]))

    def test_missing_runtime_call_edge_fails(self):
        raw = copy.deepcopy(self.raw)
        raw["edges"] = [e for e in raw["edges"] if e["relation"] != "calls"]
        result = self.check(raw=raw)
        self.assertEqual(result["status"], "FAIL")
        self.assertTrue(any(e.get("code") == "RAW_SEMANTIC_EDGE_MISSING_OR_DUPLICATED" and e.get("relation") == "calls" for e in result["errors"]))

    def test_wrong_inheritance_target_fails(self):
        raw = copy.deepcopy(self.raw)
        raw["edges"][2]["target"] = "ghost_base"
        result = self.check(raw=raw)
        self.assertEqual(result["status"], "FAIL")
        self.assertTrue(any(e.get("code") == "RAW_SEMANTIC_EDGE_MISSING_OR_DUPLICATED" and e.get("relation") == "inherits" for e in result["errors"]))

    def test_candidate_cannot_contain_held_inferred_edge(self):
        candidate = copy.deepcopy(self.candidate)
        candidate["edges"].append(copy.deepcopy(self.edges[3]))
        result = self.check(candidate=candidate)
        self.assertEqual(result["status"], "FAIL")
        self.assertTrue(any(e.get("code") == "HELD_INFERRED_EDGE_LEAKED_INTO_CANDIDATE" for e in result["errors"]))

    def test_owner_hold_must_remain_confirmed(self):
        manifest = copy.deepcopy(self.manifest)
        manifest["edge_decisions"][0]["owner_confirmation"] = "PENDING"
        result = self.check(manifest=manifest)
        self.assertEqual(result["status"], "FAIL")
        self.assertTrue(any(e.get("code") == "HELD_INFERRED_EDGE_OR_OWNER_DECISION_NOT_PRESERVED" for e in result["errors"]))

    def test_duplicate_imported_symbol_definitions_fail_closed(self):
        path = self.root / "src/contract_guard.py"
        path.write_text(self.guard + "\nclass DesignToken:\n    pass\n", encoding="utf-8")
        result = self.check()
        self.assertEqual(result["status"], "FAIL")
        self.assertTrue(any(e.get("code") == "INTERNAL_IMPORT_NOT_UNIQUELY_RESOLVED" for e in result["errors"]))

    def test_unimported_external_module_is_not_misclassified_as_internal(self):
        path = self.root / "src/outfit_flow.py"
        path.write_text("from dataclasses import dataclass\n\ndef select_outfit(x):\n    return dataclass\n", encoding="utf-8")
        result = self.check()
        from scripts.validate_canonical_semantics import _collect_imports, _definitions, _read_sources
        sources = _read_sources(self.root)
        imports, import_errors = _collect_imports(sources, _definitions(sources))
        self.assertEqual(import_errors, [])
        self.assertFalse(any(item["imported_name"] == "dataclass" for item in imports))


if __name__ == "__main__":
    unittest.main()
