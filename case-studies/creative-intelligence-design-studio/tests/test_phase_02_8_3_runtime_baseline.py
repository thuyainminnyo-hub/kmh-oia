import ast
import hashlib
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BASELINE = ROOT / "contracts" / "phase-02-8.3-runtime-baseline.json"
SCAN_ROOT = ROOT / "graphify-phase-02-8.3-sandbox"


def git_blob_sha(path: Path) -> str:
    content = path.read_bytes()
    header = f"blob {len(content)}\\0".encode("ascii")
    return hashlib.sha1(header + content).hexdigest()


class Phase0283FrozenRuntimeBaselineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads(BASELINE.read_text(encoding="utf-8"))

    def test_scan_snapshot_has_exact_approved_file_set(self):
        snapshot = self.data["scan_snapshot"]
        actual = sorted(
            path.relative_to(SCAN_ROOT).as_posix()
            for path in SCAN_ROOT.rglob("*")
            if path.is_file() or path.is_symlink()
        )
        expected = sorted(item["path"] for item in snapshot["files"])
        self.assertEqual(actual, expected)
        self.assertEqual(len(actual), 9)
        self.assertFalse(any(path.is_symlink() for path in SCAN_ROOT.rglob("*")))

    def test_every_file_matches_frozen_git_blob_sha(self):
        for item in self.data["scan_snapshot"]["files"]:
            path = SCAN_ROOT / item["path"]
            self.assertEqual(git_blob_sha(path), item["git_blob_sha"], item["path"])

    def test_eight_python_sources_are_parseable(self):
        source_files = self.data["scan_snapshot"]["source_files"]
        self.assertEqual(len(source_files), 8)
        for relative in source_files:
            ast.parse((SCAN_ROOT / relative).read_text(encoding="utf-8"), filename=relative)

    def test_ten_cross_file_semantic_expectations_are_versioned(self):
        matrix = self.data["coverage_matrix"]
        self.assertEqual(len(matrix), 10)
        self.assertTrue(any("nested_function" in item["name"] for item in matrix))
        self.assertTrue(any("function_local_relative_import" in item["name"] for item in matrix))
        self.assertEqual(
            sum(1 for item in matrix if item["relation"] == "inherits"),
            5,
        )

    def test_package_names_same_definition_labels_but_keep_distinct_files(self):
        files = set(self.data["scan_snapshot"]["source_files"])
        self.assertIn("src/phase_02_8_3/pkg_alpha/types.py", files)
        self.assertIn("src/phase_02_8_3/pkg_beta/types.py", files)
        same_name = [
            item for item in self.data["coverage_matrix"]
            if item["imported_name"] == "Widget"
        ]
        self.assertTrue(any(item["target_file"].endswith("pkg_alpha/types.py") for item in same_name))
        self.assertTrue(any(item["target_file"].endswith("pkg_beta/types.py") for item in same_name))

    def test_baseline_stays_pending_owner_approval(self):
        self.assertEqual(
            self.data["status"],
            "FROZEN_SYNTHETIC_SCAN_MANIFEST_PENDING_OWNER_APPROVAL",
        )
        self.assertFalse(self.data["policies"]["global_merge"])
        self.assertFalse(self.data["policies"]["production_promotion"])
        self.assertTrue(self.data["policies"]["new_graph_extraction_requires_fresh_owner_approval"])


if __name__ == "__main__":
    unittest.main()
