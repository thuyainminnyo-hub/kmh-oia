import unittest
from src.adaptation_engine import AdaptationEngine
from src.adaptation_command_bridge import AdaptationCommandBridge
from src.live_operating_console import LiveOperatingConsole
from src.operating_memory import OperatingMemoryRecord

class AdaptationCommandBridgeTests(unittest.TestCase):
    def test_approved_adaptation_becomes_command(self):
        r=OperatingMemoryRecord("cmd-1","2026-10-05T00:00:00+00:00","goal","execution","result","pass","decision","lesson","change","next",0.9)
        p=AdaptationEngine().propose(r, pattern="repeat", problem="defect", proposed_change="Add QA gate", expected_effect="Lower rework", next_experiment="Run for 5 commands")
        a=AdaptationEngine().approve(p)
        c=LiveOperatingConsole(date="2026-10-05")
        applied=AdaptationCommandBridge().apply(c,a,owner="human")
        command=c.snapshot().commands[0]
        self.assertEqual(command.id, applied.command_id)
        self.assertEqual(command.objective, "Add QA gate")
        self.assertEqual(command.next_action, "Run for 5 commands")

    def test_rejects_unapproved_adaptation(self):
        r=OperatingMemoryRecord("cmd-1","2026-10-05T00:00:00+00:00","goal","execution","result","pass","decision","lesson","change","next",0.9)
        p=AdaptationEngine().propose(r, pattern="repeat", problem="defect", proposed_change="Add QA gate", expected_effect="Lower rework", next_experiment="Run for 5 commands")
        with self.assertRaises(ValueError):
            AdaptationCommandBridge().apply(LiveOperatingConsole(date="2026-10-05"),p)
