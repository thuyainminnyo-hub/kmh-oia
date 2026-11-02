import copy
import hashlib
import json
import unittest

from scripts.review_graphify_edges import ReviewError, build_candidate, edge_fingerprint, edge_identity


class GraphReviewTests(unittest.TestCase):
    def setUp(self):
        self.graph = {
            "nodes": [
                {"id": "source", "label": "select_outfit", "source_file": "src/outfit_flow.py", "source_location": "L6"},
                {"id": "target", "label": "DesignToken", "source_file": "src/contract_guard.py", "source_location": "L7"},
            ],
            "edges": [
                {"source": "source", "target": "target", "relation": "references", "context": "parameter_type",
                 "confidence": "EXTRACTED", "source_file": "src/outfit_flow.py", "source_location": "L6"},
                {"source": "source", "target": "target", "relation": "uses", "confidence": "INFERRED",
                 "confidence_score": 0.95, "source_file": "src/outfit_flow.py", "source_location": "L6"},
            ],
            "hyperedges": [],
            "multigraph": True,
        }
        self.raw_bytes = json.dumps(self.graph, indent=2).encode() + b"\n"
        inferred = self.graph["edges"][1]
        extracted = self.graph["edges"][0]
        self.manifest = {
            "source_artifact": {"graph_sha256": hashlib.sha256(self.raw_bytes).hexdigest(), "workflow_run_id": 123},
            "edge_decisions": [{
                "edge_fingerprint": edge_fingerprint(inferred),
                "edge_identity": edge_identity(inferred),
                "disposition": "HOLD_NOT_PROMOTED",
                "reason_code": "INFERRED_EDGE_REQUIRES_INDEPENDENT_SEMANTIC_REVIEW",
                "rationale": "The pinned Graphify cross-file resolver emits an inferred uses edge for a reference to an imported name; retain it under review pending semantic confirmation.",
                "related_extracted_edge": edge_identity(extracted),
                "owner_confirmation": "PENDING",
            }],
        }

    def test_extracted_only_candidate_excludes_inferred_edge(self):
        candidate, report = build_candidate(self.raw_bytes, self.graph, self.manifest)
        self.assertEqual(len(candidate["nodes"]), 2)
        self.assertEqual(len(candidate["edges"]), 1)
        self.assertEqual(candidate["edges"][0]["relation"], "references")
        self.assertEqual(report["promotion_status"], "CANDIDATE_ONLY_OWNER_CONFIRMATION_PENDING")
        self.assertEqual(report["candidate_graph_counts"]["confidence"], {"EXTRACTED": 1})
        self.assertEqual(len(report["excluded_edges"]), 1)

    def test_raw_graph_is_not_mutated(self):
        before = copy.deepcopy(self.graph)
        build_candidate(self.raw_bytes, self.graph, self.manifest)
        self.assertEqual(self.graph, before)

    def test_changed_raw_graph_hash_is_rejected(self):
        changed = dict(self.graph)
        changed["extra"] = "tampered"
        with self.assertRaisesRegex(ReviewError, "SHA-256"):
            build_candidate(json.dumps(changed).encode(), changed, self.manifest)

    def test_unreviewed_inferred_edge_is_rejected(self):
        with self.assertRaisesRegex(ReviewError, "no explicit review decision"):
            build_candidate(self.raw_bytes, self.graph, {**self.manifest, "edge_decisions": []})

    def test_decision_for_missing_edge_is_rejected(self):
        manifest = copy.deepcopy(self.manifest)
        manifest["edge_decisions"][0]["edge_identity"]["relation"] = "not-a-real-edge"
        with self.assertRaisesRegex(ReviewError, "does not match"):
            build_candidate(self.raw_bytes, self.graph, manifest)

    def test_non_extracted_edge_cannot_be_promoted(self):
        manifest = copy.deepcopy(self.manifest)
        manifest["edge_decisions"][0]["disposition"] = "ACCEPT_FOR_PROMOTION"
        with self.assertRaisesRegex(ReviewError, "cannot be promoted"):
            build_candidate(self.raw_bytes, self.graph, manifest)

    def test_owner_confirmation_must_be_pending_or_confirmed_hold(self):
        manifest = copy.deepcopy(self.manifest)
        manifest["edge_decisions"][0]["owner_confirmation"] = "APPROVED"
        with self.assertRaisesRegex(ReviewError, "PENDING or CONFIRMED_HOLD"):
            build_candidate(self.raw_bytes, self.graph, manifest)

    def test_confirmed_hold_keeps_inferred_edge_excluded(self):
        manifest = copy.deepcopy(self.manifest)
        manifest["edge_decisions"][0]["owner_confirmation"] = "CONFIRMED_HOLD"
        candidate, report = build_candidate(self.raw_bytes, self.graph, manifest)
        self.assertEqual(len(candidate["edges"]), 1)
        self.assertEqual(candidate["edges"][0]["relation"], "references")
        self.assertEqual(report["owner_confirmation"], "CONFIRMED_HOLD")
        self.assertEqual(report["promotion_status"], "CANDIDATE_ONLY_HOLD_CONFIRMED_NOT_PROMOTED")
        self.assertEqual(report["production_promotion"], "NOT_AUTHORIZED")

    def test_duplicate_edge_identity_is_rejected(self):
        graph = copy.deepcopy(self.graph)
        graph["edges"].append(copy.deepcopy(graph["edges"][0]))
        raw = json.dumps(graph, indent=2).encode() + b"\n"
        manifest = copy.deepcopy(self.manifest)
        manifest["source_artifact"]["graph_sha256"] = hashlib.sha256(raw).hexdigest()
        with self.assertRaisesRegex(ReviewError, "duplicate edge identities"):
            build_candidate(raw, graph, manifest)


if __name__ == "__main__":
    unittest.main()
