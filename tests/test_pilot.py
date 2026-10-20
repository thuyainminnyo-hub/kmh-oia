"""Tests for the controlled runtime-to-evidence pilot."""
import json
import tempfile
import unittest
from pathlib import Path

from src.evidence_store import JsonlEvidenceStore
from src.pilot import run_pilot


class ControlledPilotTests(unittest.TestCase):
    def test_real_runtime_run_produces_inspectable_artifact_and_evidence(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            output, evidence, payload = run_pilot(
                "controlled pilot hello",
                artifact_dir=root / "artifacts",
                evidence_path=root / "evidence.jsonl",
                session_id="test-pilot",
            )

            self.assertEqual(output, "controlled pilot hello")
            self.assertEqual(payload["output"], output)
            self.assertEqual(payload["session_id"], "test-pilot")
            self.assertEqual(evidence.validation_state, "OBSERVED")
            self.assertEqual(evidence.run_id, payload["run_id"])
            self.assertEqual(evidence.trace_id, payload["trace_id"])
            self.assertIn("response", payload["stages"])
            self.assertIn("trace", payload["stages"])

            artifact_path = Path(evidence.artifact_ref)
            self.assertTrue(artifact_path.exists())
            stored_payload = json.loads(artifact_path.read_text(encoding="utf-8"))
            self.assertEqual(stored_payload["run_id"], evidence.run_id)
            self.assertEqual(stored_payload["output"], output)

            store = JsonlEvidenceStore(root / "evidence.jsonl")
            self.assertEqual(store.get(evidence.evidence_id), evidence)
            self.assertEqual(store.list_by_trace(evidence.trace_id), [evidence])

    def test_pilot_keeps_execution_record_observed_not_verified(self):
        with tempfile.TemporaryDirectory() as directory:
            _, evidence, _ = run_pilot(
                "pilot state boundary",
                artifact_dir=Path(directory) / "artifacts",
                evidence_path=Path(directory) / "evidence.jsonl",
            )
            self.assertEqual(evidence.validation_state, "OBSERVED")
            self.assertEqual(evidence.source_revision, "unresolved")
            self.assertIsNone(evidence.validation_ref)
            self.assertIsNone(evidence.outcome_ref)


    def test_blank_source_revision_is_rejected_before_execution(self):
        with self.assertRaisesRegex(ValueError, "source_revision"):
            run_pilot(
                "this should not execute",
                source_revision="   ",
            )



if __name__ == "__main__":
    unittest.main()
