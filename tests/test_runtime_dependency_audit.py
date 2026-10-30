#!/usr/bin/env python3
"""Tests for the Python runtime dependency inventory gate."""
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.audit_python_dependencies import audit


class RuntimeDependencyAuditTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.src = self.root / "src"
        self.src.mkdir()
        (self.root / "requirements-runtime.txt").write_text(
            "# no third-party runtime dependencies at this checkpoint\n",
            encoding="utf-8",
        )

    def tearDown(self):
        self.temp.cleanup()

    def write_source(self, name, content):
        path = self.src / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    def test_standard_library_and_first_party_imports_pass(self):
        self.write_source("__init__.py", "import json\nfrom pathlib import Path\nfrom src.state import State\n")
        result = audit(self.root)
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["source_files_scanned"], 1)
        self.assertEqual(result["stdlib_import_roots"], ["json", "pathlib"])
        self.assertEqual(result["local_import_roots"], ["src"])
        self.assertEqual(result["third_party_import_roots"], [])

    def test_undeclared_third_party_import_holds(self):
        self.write_source("service.py", "import requests\n")
        result = audit(self.root)
        self.assertEqual(result["status"], "HOLD")
        self.assertEqual(result["undeclared_runtime_distributions"], ["requests"])

    def test_declared_exact_third_party_import_passes(self):
        self.write_source("service.py", "import jsonschema\n")
        (self.root / "requirements-runtime.txt").write_text("jsonschema==4.26.0\n", encoding="utf-8")
        result = audit(self.root)
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["declared_runtime_distributions"], {"jsonschema": "4.26.0"})

    def test_import_name_maps_to_distribution_name(self):
        self.write_source("service.py", "import yaml\n")
        (self.root / "requirements-runtime.txt").write_text("PyYAML==6.0.3\n", encoding="utf-8")
        result = audit(self.root)
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["declared_runtime_distributions"], {"pyyaml": "6.0.3"})

    def test_unpinned_runtime_requirement_is_rejected(self):
        self.write_source("service.py", "import requests\n")
        (self.root / "requirements-runtime.txt").write_text("requests>=2.0\n", encoding="utf-8")
        result = audit(self.root)
        self.assertEqual(result["status"], "HOLD")
        self.assertTrue(result["errors"])

    def test_dynamic_import_limit_is_disclosed(self):
        self.write_source("service.py", "import importlib\nmodule = importlib.import_module('optional_plugin')\n")
        result = audit(self.root)
        self.assertEqual(result["status"], "PASS")
        self.assertTrue(any("dynamic imports" in item for item in result["limitations"]))


if __name__ == "__main__":
    unittest.main()
