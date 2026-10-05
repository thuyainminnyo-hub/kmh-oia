import unittest

from src.live_operating_console import LiveOperatingConsole
from src.live_runtime_bridge import LiveRuntimeBridge
from src.next_action_command_materializer import NextActionCommandMaterializer
from src.next_action_engine import NextAction


class NextActionRuntimeProvenanceTests(unittest.TestCase):
    def test_provenance_survives_materialization_and_runtime(self):
        console = LiveOperatingConsole(date="2026-10-05", primary_objective="Today")
        action = NextAction("DECISION", 4, "Review decision", "governance backlog")
        materialized = NextActionCommandMaterializer().materialize(
            action, console, owner="system", expected_output="decision reviewed"
        )
        record = LiveRuntimeBridge(console).execute(materialized.command.id)

        self.assertEqual(record.final_status, "LEARNED")
        self.assertIn("source_action_kind=DECISION", record.evidence)
        self.assertIn("source_action_priority=4", record.evidence)
        self.assertIn("source_action_reason=governance backlog", record.evidence)


if __name__ == "__main__":
    unittest.main()
