import unittest

from src.live_operating_console import LiveOperatingConsole


class LiveOperatingConsoleTests(unittest.TestCase):
    def setUp(self) -> None:
        self.console = LiveOperatingConsole(
            date="2026-10-05",
            primary_objective="Ship the highest-leverage work",
        )
        self.command = self.console.add_command(
            objective="Implement live execution flow",
            priority="P1",
            owner="Human + AI",
            expected_output="Verified execution",
            next_action="Start runtime task",
        )

    def test_happy_path_requires_evidence_before_verification(self) -> None:
        self.console.transition(self.command.id, "QUALIFIED")
        self.console.transition(self.command.id, "READY")
        self.console.transition(self.command.id, "ACTIVE")
        self.console.transition(self.command.id, "COMPLETED")

        with self.assertRaises(ValueError):
            self.console.verify(self.command.id, passed=True)

        self.console.attach_evidence(self.command.id, "trace-001")
        self.console.verify(self.command.id, passed=True)
        self.assertEqual(self.command.status, "VERIFIED")

        self.console.record_learning(
            self.command.id,
            "Evidence-first verification prevents false completion.",
        )
        self.assertEqual(self.command.status, "LEARNED")

    def test_failed_qa_returns_to_rework(self) -> None:
        for status in ("QUALIFIED", "READY", "ACTIVE", "COMPLETED"):
            self.console.transition(self.command.id, status)
        self.console.attach_evidence(self.command.id, "artifact-001")
        self.console.verify(self.command.id, passed=False, note="Fix defect")
        self.assertEqual(self.command.status, "REWORK")
        self.assertEqual(self.command.qa_status, "FAIL")

    def test_snapshot_exposes_operational_state(self) -> None:
        self.console.transition(self.command.id, "QUALIFIED")
        self.console.transition(self.command.id, "READY")
        self.console.transition(self.command.id, "ACTIVE")
        snapshot = self.console.snapshot()
        self.assertEqual(snapshot.primary_objective, "Ship the highest-leverage work")
        self.assertEqual(len(snapshot.commands), 1)
        self.assertEqual(snapshot.commands[0].status, "ACTIVE")


if __name__ == "__main__":
    unittest.main()
