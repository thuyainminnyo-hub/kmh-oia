import unittest

from src.live_operating_console import LiveOperatingConsole
from src.live_runtime_bridge import LiveRuntimeBridge
from src.standardization_engine import OperatingStandard
from src.receipt_replay_store import SQLiteReceiptReplayStore
import tempfile
from pathlib import Path


class LiveRuntimeBridgeTests(unittest.TestCase):
    def test_command_runs_through_runtime_and_becomes_learned(self) -> None:
        console = LiveOperatingConsole(
            date="2026-10-05",
            primary_objective="Execute today's highest-leverage command",
        )
        command = console.add_command(
            objective="hello operating intelligence",
            priority="P1",
            owner="Human + AI",
            expected_output="runtime response",
        )

        record = LiveRuntimeBridge(console).execute(command.id)

        self.assertEqual(record.final_status, "LEARNED")
        self.assertEqual(record.qa_status, "PASS")
        self.assertIn("input_gateway", record.trace_stages)
        self.assertIn("evaluation", record.trace_stages)
        self.assertTrue(any(item.startswith("trace_id=") for item in record.evidence))

    def test_governed_execution_feeds_evidence_back_to_control_plane(self) -> None:
        console = LiveOperatingConsole(date="2026-10-05", primary_objective="Governed execution")
        command = console.add_command(
            objective="execute governed work",
            priority="P1",
            owner="system",
            expected_output="runtime response",
        )
        standard = OperatingStandard(
            "std:a:v1", "a", "Require evidence", "Higher quality", 1, "ACTIVE"
        )

        record = LiveRuntimeBridge(console).execute(
            command.id, standard=standard, applied_rule="Require evidence"
        )

        self.assertIsNotNone(record.standard_feedback)
        self.assertFalse(record.standard_feedback.drift.drifted)
        self.assertIsNone(record.standard_feedback.trigger)


    def test_durable_replay_store_required_rejects_missing_store(self):
        console = LiveOperatingConsole(date="2026-10-21", primary_objective="Replay guard startup")
        with self.assertRaisesRegex(ValueError, "durable receipt_replay_store is required"):
            LiveRuntimeBridge(console, require_durable_replay_store=True)

    def test_durable_replay_store_required_rejects_unhealthy_sqlite_schema(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = str(Path(tmp) / "replay.sqlite3")
            store = SQLiteReceiptReplayStore(path)
            with __import__("sqlite3").connect(path) as connection:
                connection.execute("DROP TABLE receipt_replay_claims")
            console = LiveOperatingConsole(date="2026-10-21", primary_objective="Replay guard startup")
            with self.assertRaisesRegex(ValueError, "health check failed"):
                LiveRuntimeBridge(
                    console, receipt_replay_store=store, require_durable_replay_store=True
                )

    def test_outcome_linked_request_without_trusted_adapter_cannot_admit_learning(self):
        console = LiveOperatingConsole(
            date="2026-10-21",
            primary_objective="Admission gate integration",
        )
        command = console.add_command(
            objective="exercise evidence admission",
            priority="P1",
            owner="system",
            expected_output="runtime response",
        )
        bridge = LiveRuntimeBridge(console)
        record = bridge.execute(
            command.id,
            evidence_source="caller-supplied-source",
            raw_observation="caller-supplied outcome=success",
            verification_status="OUTCOME_LINKED",
            outcome_linked=True,
            source_authenticated=True,
            attribution_verified=True,
            source_record_id="caller-source-record",
        )

        self.assertEqual(record.final_status, "LEARNED")
        self.assertEqual(record.admission.decision, "NOT_ADMITTED")
        self.assertFalse(record.admission.learning_admitted)
        self.assertEqual(record.admission.trusted_receipt_content_hash, "")
        self.assertIsNotNone(record.trusted_receipt_verification)
        self.assertFalse(record.trusted_receipt_verification.verified)
        # Runtime may retain an internal observation for audit, but the gate must
        # not represent caller booleans or metadata as a trusted outcome receipt.

    def test_unknown_command_is_rejected(self) -> None:
        console = LiveOperatingConsole(date="2026-10-05")
        bridge = LiveRuntimeBridge(console)

        with self.assertRaises(KeyError):
            bridge.execute("missing-command")


if __name__ == "__main__":
    unittest.main()
