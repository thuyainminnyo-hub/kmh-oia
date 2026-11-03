import ast
import hashlib
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "contracts" / "phase-02-8.3-v09101-candidate.json"
SCAN_ROOT = ROOT / "graphify-phase-02-8.3-v09101-candidate"


def git_blob_sha(path: Path) -> str:
    content = path.read_bytes()
    header = b"blob " + str(len(content)).encode("ascii") + bytes([0])
    return hashlib.sha1(header + content).hexdigest()


class Phase0283GraphifyV09101CandidateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads(CONTRACT.read_text(encoding="utf-8"))

    def test_exact_candidate_snapshot_and_blob_hashes(self):
        files = self.data["fixture"]["files"]
        actual = sorted(
            path.relative_to(SCAN_ROOT).as_posix()
            for path in SCAN_ROOT.rglob("*")
            if path.is_file() or path.is_symlink()
        )
        expected = sorted(item["path"] for item in files)
        self.assertEqual(actual, expected)
        self.assertEqual(len(actual), 3)
        self.assertFalse(any(p.is_symlink() for p in SCAN_ROOT.rglob("*")))
        for item in files:
            self.assertEqual(
                git_blob_sha(SCAN_ROOT / item["path"]),
                item["git_blob_sha"],
                item["path"],
            )

    def test_pep420_namespace_layout_has_no_init_files(self):
        expected = self.data["fixture"]["package_layout"]
        self.assertIn("PEP 420", expected)
        self.assertIn("separate src/", expected)
        self.assertFalse(list(SCAN_ROOT.rglob("__init__.py")))
        self.assertTrue((SCAN_ROOT / "pkgsql/src/airflow/sql/hooks/sql.py").is_file())
        self.assertTrue((SCAN_ROOT / "pkgpresto/src/airflow/presto/hooks/presto.py").is_file())

    def test_candidate_source_files_are_valid_python(self):
        source_files = [
            item["path"] for item in self.data["fixture"]["files"]
            if item["path"].endswith(".py")
        ]
        self.assertEqual(len(source_files), 2)
        for relative in source_files:
            ast.parse((SCAN_ROOT / relative).read_text(encoding="utf-8"), filename=relative)

    def test_fixture_contains_cross_src_import_and_inheritance(self):
        path = SCAN_ROOT / "pkgpresto/src/airflow/presto/hooks/presto.py"
        tree = ast.parse(path.read_text(encoding="utf-8"))
        imports = [
            node for node in tree.body
            if isinstance(node, ast.ImportFrom)
        ]
        self.assertEqual(len(imports), 1)
        self.assertEqual(imports[0].module, "airflow.sql.hooks.sql")
        self.assertEqual(
            {alias.name for alias in imports[0].names},
            {"DbApiHook", "free_fn", "get_build_status"},
        )
        cls = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == "PrestoHook")
        self.assertEqual([base.id for base in cls.bases if isinstance(base, ast.Name)], ["DbApiHook"])

    def test_bare_call_collision_is_present_for_candidate_check(self):
        path = SCAN_ROOT / "pkgpresto/src/airflow/presto/hooks/presto.py"
        tree = ast.parse(path.read_text(encoding="utf-8"))
        cls = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == "PrestoHook")
        methods = {node.name: node for node in cls.body if isinstance(node, ast.FunctionDef)}
        self.assertIn("get_build_status", methods)
        calls = [
            node.func.id for node in ast.walk(methods["get_build_status"])
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
        ]
        self.assertIn("get_build_status", calls)
        self.assertTrue(any(alias.name == "get_build_status" for node in tree.body
                            if isinstance(node, ast.ImportFrom) for alias in node.names))

    def test_v09101_candidate_is_separate_from_v0100_baseline(self):
        candidate = self.data["candidate"]
        baseline = self.data["frozen_baseline"]
        self.assertEqual(candidate["package_version"], "0.9.101")
        self.assertEqual(candidate["source_commit"], "8e6a6d2129d4aeffc7a0e9ed79b153f7f057f42b")
        self.assertEqual(candidate["ast_cache_schema"], 36)
        self.assertEqual(baseline["version"], "0.9.100")
        self.assertEqual(baseline["ast_cache_schema"], 33)
        self.assertTrue(baseline["immutable"])
        self.assertEqual(candidate["tag_signature"], "UNSIGNED")

    def test_candidate_research_does_not_authorize_install_or_extraction(self):
        self.assertEqual(self.data["status"], "CANDIDATE_RESEARCH_ONLY_PENDING_OWNER_APPROVAL")
        self.assertFalse(self.data["runtime_execution_authorized"])
        self.assertEqual(self.data["extraction_count"], 0)
        plan = self.data["execution_plan"]
        self.assertFalse(plan["graphify_install_allowed"])
        self.assertFalse(plan["graphify_extraction_allowed"])
        self.assertEqual(plan["max_runs"], 1)
        self.assertFalse(plan["rerun_allowed"])
        governance = self.data["governance"]
        self.assertEqual(governance["g4_owner_hold"], "PRESERVED")
        self.assertTrue(governance["fresh_owner_approval_required"])
        self.assertFalse(governance["production_promotion"])


if __name__ == "__main__":
    unittest.main()
