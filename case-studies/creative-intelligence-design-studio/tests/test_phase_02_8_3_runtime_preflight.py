import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "contracts" / "phase-02-8.3-runtime-preflight.json"


class Phase0283RuntimePreflightContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads(CONTRACT.read_text(encoding="utf-8"))

    def test_pinned_graphify_source_and_lock_are_exact(self):
        source = self.data["source"]
        self.assertEqual(source["tag"], "v0.9.100")
        self.assertEqual(source["commit"], "f5155badddaa3286c78a51653791131e9e2e4d29")
        self.assertEqual(source["package"], "graphifyy")
        self.assertEqual(source["package_version"], "0.9.100")
        self.assertEqual(source["uv_version"], "0.13.6")
        self.assertEqual(source["uv_lock_blob"], "1fd2344a28be6b14c4f6f41c4901c70cadc2be0e")
        self.assertIn("--frozen", source["install_command"])

    def test_runtime_arguments_preserve_raw_graph_evidence(self):
        command = self.data["command"]
        flags = command["flags"]
        self.assertIn("--force", flags)
        self.assertIn("--code-only", flags)
        self.assertIn("--no-dedup", flags)
        self.assertIn("--no-cluster", flags)
        self.assertIn("--out", flags)
        self.assertIn("--dedup-llm", self.data["command"]["forbidden_flags"][1])

    def test_environment_is_isolated_and_model_free(self):
        env = self.data["environment"]
        self.assertTrue(env["clean_git_clone"])
        self.assertTrue(env["clean_venv"])
        self.assertTrue(env["isolated_home_under_runner_temp"])
        self.assertTrue(env["isolated_tmpdir_under_runner_temp"])
        self.assertTrue(env["scan_snapshot_read_only"])
        self.assertTrue(env["output_outside_scan_root"])
        self.assertFalse(env["model_credentials"])
        self.assertEqual(env["semantic_backend"], "none")

    def test_cache_schema_and_version_namespace_are_recorded(self):
        cache = self.data["cache"]
        self.assertEqual(
            cache["ast_cache_namespaced_by"],
            ["package_version", "ast_cache_schema", "tree_sitter_grammar_fingerprint"],
        )
        self.assertEqual(cache["pinned_ast_cache_schema"], 33)
        self.assertTrue(cache["clean_work_root_required"])
        self.assertTrue(cache["record_grammar_fingerprint"])
        self.assertTrue(cache["semantic_pass_skipped_by_code_only"])

    def test_preflight_requires_fresh_single_run_approval(self):
        self.assertEqual(self.data["status"], "PENDING_OWNER_APPROVAL")
        self.assertFalse(self.data["extraction_authorized"])
        self.assertEqual(self.data["execution_count"], 0)
        gates = self.data["preflight_gates"]
        self.assertTrue(any("fresh owner approval" in item for item in gates))
        self.assertTrue(any("no prior extraction run" in item for item in gates))
        self.assertTrue(any("run_attempt equals 1" in item for item in gates))

    def test_governance_never_promotes_or_mutates_global_graphs(self):
        governance = self.data["governance"]
        self.assertFalse(governance["raw_graph_mutation"])
        self.assertFalse(governance["existing_phase_02_5_graph_mutation"])
        self.assertFalse(governance["candidate_global_merge"])
        self.assertFalse(governance["inferred_promotion"])
        self.assertFalse(governance["ambiguous_promotion"])
        self.assertFalse(governance["oia_runtime_integration"])
        self.assertFalse(governance["production_promotion"])
        self.assertEqual(governance["g4_owner_hold"], "PRESERVED")
        self.assertTrue(governance["fresh_owner_approval_required"])


if __name__ == "__main__":
    unittest.main()
