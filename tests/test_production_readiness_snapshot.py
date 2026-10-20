import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from scripts.production_readiness_snapshot import build_readiness_snapshot


class ProductionReadinessSnapshotTests(unittest.TestCase):
    def test_repository_contracts_pass_when_required_files_exist(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            for item in (
                "src/production_evidence_runtime.py",
                "src/receipt_replay_store.py",
                "src/trusted_source_receipt.py",
                "scripts/deployment_preflight.py",
                "docs/runbooks/production-evidence-runtime.md",
            ):
                path = root / item
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("# test fixture", encoding="utf-8")

            result = build_readiness_snapshot(root)
            by_name = {item["gate"]: item for item in result["gates"]}
            self.assertEqual(by_name["repository_contracts"]["status"], "PASS")
            self.assertEqual(by_name["live_deployment"]["status"], "NOT_VERIFIED")
            self.assertEqual(by_name["real_provider_authenticity_and_attribution"]["status"], "NOT_VERIFIED")
            self.assertEqual(by_name["external_business_outcome"]["status"], "HOLD")
            self.assertEqual(result["release_decision"], "HOLD")

    def test_missing_contract_files_hold_repository_gate(self):
        with TemporaryDirectory() as tmp:
            result = build_readiness_snapshot(Path(tmp))
            by_name = {item["gate"]: item for item in result["gates"]}
            self.assertEqual(by_name["repository_contracts"]["status"], "HOLD")
            self.assertEqual(len(result["required_files_missing"]), 5)
            self.assertEqual(result["release_decision"], "HOLD")

    def test_no_snapshot_can_infer_live_deployment_from_ci_like_files(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            for item in (
                "src/production_evidence_runtime.py",
                "src/receipt_replay_store.py",
                "src/trusted_source_receipt.py",
                "scripts/deployment_preflight.py",
                "docs/runbooks/production-evidence-runtime.md",
            ):
                path = root / item
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("# repository file", encoding="utf-8")
            result = build_readiness_snapshot(root)
            live = next(item for item in result["gates"] if item["gate"] == "live_deployment")
            self.assertEqual(live["status"], "NOT_VERIFIED")
            self.assertIn("cannot prove", live["evidence"])


if __name__ == "__main__":
    unittest.main()
