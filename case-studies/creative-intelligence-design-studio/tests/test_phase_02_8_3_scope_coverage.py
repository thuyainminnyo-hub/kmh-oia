import unittest
from pathlib import Path
import tempfile

from scripts.validate_phase_02_7_graph import validate_graph


class Phase0283NestedScopeCoverageTests(unittest.TestCase):
    def _validate(self, service_source, graph_nodes, graph_edges, expected_importer, expected_local):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        root = Path(temp.name)
        files = {
            ".graphifyignore": "**/.env\n",
            "src/pkg/__init__.py": "",
            "src/pkg/models.py": "class Widget:\n    pass\n",
            "src/pkg/service.py": service_source,
        }
        for relative, text in files.items():
            path = root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")

        source_files = sorted(path for path in files if path.endswith(".py"))
        raw = {
            "nodes": [
                {"id": "pkg_widget", "label": "Widget", "file_type": "code", "source_file": "src/pkg/models.py", "source_location": "L1"},
                *graph_nodes,
            ],
            "edges": graph_edges,
        }
        baseline = {
            "baseline_id": "KMH-PHASE-02.8.3-NESTED-SCOPE",
            "source_files": source_files,
            "coverage_matrix": [{
                "name": "nested-imported-widget",
                "importer_file": "src/pkg/service.py",
                "imported_name": "Widget",
                "target_file": "src/pkg/models.py",
                "category": "TYPE_ANNOTATION",
                "relation": "references",
            }],
        }
        report, candidate = validate_graph(raw, root, baseline)
        self.assertIsNotNone(candidate)
        self.assertEqual(report["status"], "PASS_WITH_WARNINGS", report["errors"])
        nested_links = [
            link for link in report["canonical_semantic_links"]
            if link["source_symbol"] == expected_importer
            and link["local_name"] == expected_local
            and link["relation"] == "references"
        ]
        self.assertEqual(len(nested_links), 1)
        self.assertEqual(nested_links[0]["target_node_id"], "pkg_widget")
        self.assertEqual(nested_links[0]["raw_extracted_edge_matches"], 1)
        return report

    def test_module_import_is_validated_inside_nested_function(self):
        source = (
            "from .models import Widget as W\n"
            "\n"
            "def outer():\n"
            "    def inner(value: W):\n"
            "        return value\n"
            "    return inner\n"
        )
        nodes = [
            {"id": "service_outer", "label": "outer()", "file_type": "code", "source_file": "src/pkg/service.py", "source_location": "L3"},
            {"id": "service_inner", "label": "inner()", "file_type": "code", "source_file": "src/pkg/service.py", "source_location": "L4"},
        ]
        edges = [{
            "source": "service_inner",
            "target": "pkg_widget",
            "relation": "references",
            "context": "parameter_type",
            "confidence": "EXTRACTED",
            "source_file": "src/pkg/service.py",
            "source_location": "L4",
        }]
        report = self._validate(source, nodes, edges, "inner()", "W")
        self.assertEqual(report["canonical_semantic_links"][0]["source_symbol"], "inner()")

    def test_function_local_relative_import_is_scoped_to_descendants(self):
        source = (
            "def outer():\n"
            "    from .models import Widget as W\n"
            "    def inner(value: W):\n"
            "        return value\n"
            "    return inner\n"
            "\n"
            "def sibling(value: W):\n"
            "    return value\n"
        )
        nodes = [
            {"id": "service_outer", "label": "outer()", "file_type": "code", "source_file": "src/pkg/service.py", "source_location": "L1"},
            {"id": "service_inner", "label": "inner()", "file_type": "code", "source_file": "src/pkg/service.py", "source_location": "L3"},
            {"id": "service_sibling", "label": "sibling()", "file_type": "code", "source_file": "src/pkg/service.py", "source_location": "L7"},
        ]
        edges = [{
            "source": "service_inner",
            "target": "pkg_widget",
            "relation": "references",
            "context": "parameter_type",
            "confidence": "EXTRACTED",
            "source_file": "src/pkg/service.py",
            "source_location": "L3",
        }]
        report = self._validate(source, nodes, edges, "inner()", "W")
        self.assertEqual(len(report["canonical_semantic_links"]), 1)
        self.assertNotIn("sibling()", {link["source_symbol"] for link in report["canonical_semantic_links"]})


if __name__ == "__main__":
    unittest.main()
