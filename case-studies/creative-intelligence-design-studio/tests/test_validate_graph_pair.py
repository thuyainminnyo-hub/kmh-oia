import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from scripts.validate_graph_pair import validate


class GraphPairValidationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "src").mkdir()
        flow = '"""Outfit flow fixture."""\n\nfrom contract_guard import DesignToken\n\n\ndef select_outfit(token: DesignToken):\n    return token.token_name\n'
        guard = '"""Contract guard fixture."""\n\nclass DesignToken:\n    """Design token fixture."""\n    token_name: str\n'
        (self.root / "src/outfit_flow.py").write_text(flow, encoding="utf-8")
        (self.root / "src/contract_guard.py").write_text(guard, encoding="utf-8")
        self.raw = {
            "nodes": [
                {"id": "src_outfit_flow", "label": "outfit_flow.py", "file_type": "code", "source_file": "src/outfit_flow.py", "source_location": "L1"},
                {"id": "src_outfit_flow_select_outfit", "label": "select_outfit()", "file_type": "code", "source_file": "src/outfit_flow.py", "source_location": "L6", "_callable": True},
                {"id": "src_contract_guard", "label": "contract_guard.py", "file_type": "code", "source_file": "src/contract_guard.py", "source_location": "L1"},
                {"id": "src_contract_guard_designtoken", "label": "DesignToken", "file_type": "code", "source_file": "src/contract_guard.py", "source_location": "L3", "_callable": True, "_callable_class": True},
                {"id": "dataclasses", "label": "dataclasses", "file_type": "concept", "external": True, "source_file": ""},
            ],
            "edges": [
                {"source": "src_outfit_flow", "target": "src_outfit_flow_select_outfit", "relation": "contains", "confidence": "EXTRACTED", "source_file": "src/outfit_flow.py", "source_location": "L6"},
                {"source": "src_outfit_flow_select_outfit", "target": "src_contract_guard_designtoken", "relation": "references", "context": "parameter_type", "confidence": "EXTRACTED", "source_file": "src/outfit_flow.py", "source_location": "L6"},
                {"source": "src_outfit_flow_select_outfit", "target": "src_contract_guard_designtoken", "relation": "uses", "confidence": "INFERRED", "confidence_score": 0.95, "source_file": "src/outfit_flow.py", "source_location": "L6"},
                {"source": "src_contract_guard", "target": "dataclasses", "relation": "imports_from", "confidence": "EXTRACTED", "source_file": "src/contract_guard.py", "source_location": "L1"},
            ],
            "hyperedges": [],
        }
        self.candidate = copy.deepcopy(self.raw)
        self.candidate["edges"] = [e for e in self.raw["edges"] if e["confidence"] == "EXTRACTED"]
        self.raw_bytes = json.dumps(self.raw, indent=2).encode() + b"\n"
        self.candidate_bytes = json.dumps(self.candidate, indent=2).encode() + b"\n"
        held = self.raw["edges"][2]
        identity = {k: held.get(k) for k in ("source", "target", "relation", "confidence", "source_file", "source_location")}
        fingerprint = hashlib.sha256(json.dumps(identity, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        self.manifest = {
            "review_status": "OWNER_CONFIRMED_HOLD_PENDING_ADDITIONAL_EVIDENCE",
            "source_artifact": {
                "graph_sha256": hashlib.sha256(self.raw_bytes).hexdigest(),
                "workflow_run_id": 7, "artifact_id": 9, "graphify_version": "0.9.100", "graphify_source_commit": "a" * 40,
            },
            "owner_decision": {"decision": "KEEP_INFERRED_EDGE_UNDER_REVIEW_DO_NOT_PROMOTE", "production_promotion": "NOT_AUTHORIZED"},
            "edge_decisions": [{"edge_fingerprint": fingerprint, "edge_identity": identity, "disposition": "HOLD_NOT_PROMOTED", "owner_confirmation": "CONFIRMED_HOLD"}],
        }
        self.promotion = {
            "raw_graph_sha256": hashlib.sha256(self.raw_bytes).hexdigest(),
            "candidate_graph_sha256": hashlib.sha256(self.candidate_bytes).hexdigest(),
            "owner_confirmation": "CONFIRMED_HOLD", "production_promotion": "NOT_AUTHORIZED",
            "raw_graph_counts": {"nodes": 5, "edges": 4, "confidence": {"EXTRACTED": 3, "INFERRED": 1}},
            "candidate_graph_counts": {"nodes": 5, "edges": 3, "confidence": {"EXTRACTED": 3}},
        }
        self.baseline = {
            "baseline_id": "KMH-CREATIVE-GRAPH-BASELINE-02.5-v1",
            "source_artifact": {"workflow_run_id": 7, "artifact_id": 9},
            "graphify": {"version": "0.9.100", "source_commit": "a" * 40},
            "graphs": {"raw_sha256": hashlib.sha256(self.raw_bytes).hexdigest(), "candidate_sha256": hashlib.sha256(self.candidate_bytes).hexdigest()},
            "expected_metrics": {
                "raw": {"nodes": 5, "edges": 4, "confidence": {"EXTRACTED": 3, "INFERRED": 1}},
                "candidate": {"nodes": 5, "edges": 3, "confidence": {"EXTRACTED": 3}},
            },
        }

    def check(self, raw=None, candidate=None, manifest=None, promotion=None, baseline=None):
        return validate(raw or self.raw_bytes, candidate or self.candidate_bytes,
                        manifest or self.manifest, promotion or self.promotion, self.root, baseline or self.baseline)

    def test_valid_graph_pair_and_external_reference_pass(self):
        result = self.check()
        self.assertEqual(result["status"], "PASS", result["errors"])
        self.assertEqual(result["graphs"]["raw"]["external_node_ids"], ["dataclasses"])
        self.assertFalse(result["governance"]["inferred_edge_promoted"])

    def test_raw_hash_tampering_fails(self):
        result = self.check(raw=self.raw_bytes + b" ")
        self.assertEqual(result["status"], "FAIL")
        self.assertTrue(any("raw graph SHA" in e for e in result["errors"]))

    def test_candidate_hash_tampering_fails(self):
        result = self.check(candidate=self.candidate_bytes + b" ")
        self.assertEqual(result["status"], "FAIL")
        self.assertTrue(any("candidate graph SHA" in e for e in result["errors"]))

    def test_candidate_cannot_contain_inferred_edge(self):
        graph = copy.deepcopy(self.candidate); graph["edges"].append(self.raw["edges"][2])
        data = json.dumps(graph, indent=2).encode() + b"\n"
        promotion = copy.deepcopy(self.promotion); promotion["candidate_graph_sha256"] = hashlib.sha256(data).hexdigest()
        baseline = copy.deepcopy(self.baseline); baseline["graphs"]["candidate_sha256"] = hashlib.sha256(data).hexdigest()
        baseline["expected_metrics"]["candidate"] = {"nodes": 5, "edges": 4, "confidence": {"EXTRACTED": 3, "INFERRED": 1}}
        result = self.check(candidate=data, promotion=promotion, baseline=baseline)
        self.assertEqual(result["status"], "FAIL")
        self.assertTrue(any("candidate is not the exact" in e or "non-EXTRACTED" in e for e in result["errors"]))

    def test_candidate_must_include_every_raw_extracted_edge(self):
        graph = copy.deepcopy(self.candidate); graph["edges"].pop()
        data = json.dumps(graph, indent=2).encode() + b"\n"
        promotion = copy.deepcopy(self.promotion); promotion["candidate_graph_sha256"] = hashlib.sha256(data).hexdigest()
        baseline = copy.deepcopy(self.baseline); baseline["graphs"]["candidate_sha256"] = hashlib.sha256(data).hexdigest()
        baseline["expected_metrics"]["candidate"] = {"nodes": 5, "edges": 2, "confidence": {"EXTRACTED": 2}}
        result = self.check(candidate=data, promotion=promotion, baseline=baseline)
        self.assertEqual(result["status"], "FAIL")
        self.assertTrue(any("candidate is not the exact" in e for e in result["errors"]))

    def test_duplicate_node_id_fails(self):
        graph = copy.deepcopy(self.raw); graph["nodes"].append(copy.deepcopy(graph["nodes"][0]))
        data = json.dumps(graph, indent=2).encode() + b"\n"
        manifest = copy.deepcopy(self.manifest); manifest["source_artifact"]["graph_sha256"] = hashlib.sha256(data).hexdigest()
        promotion = copy.deepcopy(self.promotion); promotion["raw_graph_sha256"] = hashlib.sha256(data).hexdigest(); promotion["raw_graph_counts"]["nodes"] = 6
        baseline = copy.deepcopy(self.baseline); baseline["graphs"]["raw_sha256"] = hashlib.sha256(data).hexdigest(); baseline["expected_metrics"]["raw"]["nodes"] = 6
        result = self.check(raw=data, manifest=manifest, promotion=promotion, baseline=baseline)
        self.assertEqual(result["status"], "FAIL")
        self.assertTrue(any("duplicate node id" in e for e in result["errors"]))

    def test_dangling_endpoint_fails(self):
        graph = copy.deepcopy(self.raw); graph["edges"][0]["target"] = "missing-node"
        data = json.dumps(graph, indent=2).encode() + b"\n"
        manifest = copy.deepcopy(self.manifest); manifest["source_artifact"]["graph_sha256"] = hashlib.sha256(data).hexdigest()
        promotion = copy.deepcopy(self.promotion); promotion["raw_graph_sha256"] = hashlib.sha256(data).hexdigest()
        baseline = copy.deepcopy(self.baseline); baseline["graphs"]["raw_sha256"] = hashlib.sha256(data).hexdigest()
        result = self.check(raw=data, manifest=manifest, promotion=promotion, baseline=baseline)
        self.assertEqual(result["status"], "FAIL")
        self.assertTrue(any("unresolved target endpoint" in e for e in result["errors"]))

    def test_ghost_symbol_at_source_anchor_fails(self):
        graph = copy.deepcopy(self.raw); graph["nodes"][1]["label"] = "ghost_function()"
        data = json.dumps(graph, indent=2).encode() + b"\n"
        manifest = copy.deepcopy(self.manifest); manifest["source_artifact"]["graph_sha256"] = hashlib.sha256(data).hexdigest()
        promotion = copy.deepcopy(self.promotion); promotion["raw_graph_sha256"] = hashlib.sha256(data).hexdigest()
        baseline = copy.deepcopy(self.baseline); baseline["graphs"]["raw_sha256"] = hashlib.sha256(data).hexdigest()
        result = self.check(raw=data, manifest=manifest, promotion=promotion, baseline=baseline)
        self.assertEqual(result["status"], "FAIL")
        self.assertTrue(any("function definition not found" in e for e in result["errors"]))

    def test_owner_hold_cannot_be_removed(self):
        manifest = copy.deepcopy(self.manifest); manifest["edge_decisions"][0]["owner_confirmation"] = "PENDING"
        result = self.check(manifest=manifest)
        self.assertEqual(result["status"], "FAIL")
        self.assertTrue(any("owner-confirmed HOLD" in e for e in result["errors"]))

    def test_unanchored_external_node_is_not_a_ghost(self):
        result = self.check()
        self.assertEqual(result["graphs"]["raw"]["ghost_node_indicator_count"], 0)
        self.assertEqual(result["graphs"]["raw"]["external_node_ids"], ["dataclasses"])

    def test_raw_input_is_never_mutated(self):
        before = copy.deepcopy(self.raw); self.check()
        self.assertEqual(self.raw, before)


if __name__ == "__main__":
    unittest.main()
