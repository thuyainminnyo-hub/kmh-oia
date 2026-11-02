import tempfile
import unittest
from pathlib import Path

from scripts.validate_graphify_output import validate_graph


class GraphifyOutputTraceabilityTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        (self.root / "src").mkdir()
        (self.root / "src" / "contract_guard.py").write_text(
            "class DesignToken:\n    pass\n\n"
            "def is_approved_token(token):\n    return bool(token)\n",
            encoding="utf-8",
        )
        (self.root / "src" / "outfit_flow.py").write_text(
            "from contract_guard import DesignToken, is_approved_token\n\n"
            "def select_outfit(token: DesignToken):\n"
            "    if not is_approved_token(token):\n"
            "        raise ValueError('not approved')\n"
            "    return token\n",
            encoding="utf-8",
        )
        self.graph = {
            "nodes": [
                {"id": "token", "label": "DesignToken", "source_file": "src/contract_guard.py", "source_location": "L1"},
                {"id": "approve", "label": "is_approved_token()", "source_file": "src/contract_guard.py", "source_location": "L4"},
                {"id": "outfit_file", "label": "outfit_flow.py", "source_file": "src/outfit_flow.py", "source_location": "L1"},
                {"id": "select", "label": "select_outfit()", "source_file": "src/outfit_flow.py", "source_location": "L3"},
            ],
            "edges": [
                {"source": "select", "target": "approve", "relation": "calls", "confidence": "EXTRACTED",
                 "source_file": "src/outfit_flow.py", "source_location": "L4"}
            ],
        }

    def test_complete_graph_passes_traceability(self):
        result = validate_graph(self.graph, self.root)
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["cross_file_edges"][0]["source"], "src/outfit_flow.py")
        self.assertEqual(result["cross_file_edges"][0]["target"], "src/contract_guard.py")

    def test_external_node_path_is_rejected(self):
        graph = {**self.graph, "nodes": [*self.graph["nodes"], {
            "id": "secret", "label": "private", "source_file": "../private/secret.py", "source_location": "L1"
        }]}
        result = validate_graph(graph, self.root)
        self.assertEqual(result["status"], "FAIL")
        self.assertTrue(any("non-allowlisted source" in x or "external or invalid source_file" in x for x in result["errors"]))

    def test_source_line_out_of_range_is_rejected(self):
        graph = {**self.graph, "nodes": [
            {**node, "source_location": "L999"} if node["id"] == "select" else node
            for node in self.graph["nodes"]
        ]}
        result = validate_graph(graph, self.root)
        self.assertTrue(any("exceeds src/outfit_flow.py length" in x for x in result["errors"]))

    def test_edge_endpoint_must_resolve(self):
        graph = {**self.graph, "edges": [{**self.graph["edges"][0], "target": "missing"}]}
        result = validate_graph(graph, self.root)
        self.assertTrue(any("target id does not resolve" in x for x in result["errors"]))

    def test_unknown_confidence_is_rejected(self):
        graph = {**self.graph, "edges": [{**self.graph["edges"][0], "confidence": "CERTAIN"}]}
        result = validate_graph(graph, self.root)
        self.assertTrue(any("invalid confidence" in x for x in result["errors"]))

    def test_edge_without_source_line_is_rejected(self):
        edge = {key: value for key, value in self.graph["edges"][0].items() if key != "source_location"}
        graph = {**self.graph, "edges": [edge]}
        result = validate_graph(graph, self.root)
        self.assertTrue(any("lacks a valid L<number> source_location" in x for x in result["errors"]))

    def test_graph_must_contain_cross_file_evidence(self):
        graph = {**self.graph, "edges": [{**self.graph["edges"][0], "target": "token"}]}
        result = validate_graph(graph, self.root)
        self.assertTrue(any("no cross-file edge" in x for x in result["errors"]))

    def test_inferred_edges_are_reported_not_promoted(self):
        graph = {**self.graph, "edges": [
            self.graph["edges"][0],
            {"source": "select", "target": "approve", "relation": "calls", "confidence": "INFERRED",
             "source_file": "src/outfit_flow.py", "source_location": "L4"},
        ]}
        result = validate_graph(graph, self.root)
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["confidence_counts"]["INFERRED"], 1)
        self.assertEqual(len(result["inferred_or_ambiguous_edges_for_review"]), 1)


if __name__ == "__main__":
    unittest.main()
