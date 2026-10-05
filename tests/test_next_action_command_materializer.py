import unittest

from src.live_operating_console import LiveOperatingConsole
from src.next_action_command_materializer import NextActionCommandMaterializer
from src.next_action_engine import NextAction


class NextActionCommandMaterializerTests(unittest.TestCase):
    def console(self):
        return LiveOperatingConsole(date="2026-10-05", primary_objective="Today")

    def test_high_priority_action_becomes_p1_inbox_command(self):
        action = NextAction("BLOCKER", 1, "Resolve blocker: API failure", "blocked")
        result = NextActionCommandMaterializer().materialize(
            action, self.console(), owner="system", expected_output="blocker resolved"
        )
        self.assertEqual(result.command.priority, "P1")
        self.assertEqual(result.command.status, "INBOX")
        self.assertEqual(result.command.expected_output, "blocker resolved")

    def test_provenance_is_preserved(self):
        action = NextAction("DECISION", 4, "Review decision", "governance backlog")
        result = NextActionCommandMaterializer().materialize(
            action, self.console(), owner="system", expected_output="decision reviewed"
        )
        self.assertEqual(result.command.source_action_kind, "DECISION")
        self.assertEqual(result.command.source_action_priority, 4)
        self.assertEqual(result.command.source_action_reason, "governance backlog")

    def test_signal_action_becomes_p2(self):
        action = NextAction("SIGNAL", 5, "Review signal", "signal")
        result = NextActionCommandMaterializer().materialize(
            action, self.console(), owner="system", expected_output="signal reviewed"
        )
        self.assertEqual(result.command.priority, "P2")

    def test_none_cannot_become_command(self):
        action = NextAction("NONE", 99, "No immediate action.", "none")
        with self.assertRaises(ValueError):
            NextActionCommandMaterializer().materialize(
                action, self.console(), owner="system", expected_output="anything"
            )

    def test_materialization_does_not_execute(self):
        console = self.console()
        action = NextAction("DECISION", 4, "Review decision", "pending")
        result = NextActionCommandMaterializer().materialize(
            action, console, owner="system", expected_output="decision reviewed"
        )
        self.assertEqual(result.command.status, "INBOX")
        self.assertEqual(console.snapshot().commands[0].status, "INBOX")


if __name__ == "__main__":
    unittest.main()
