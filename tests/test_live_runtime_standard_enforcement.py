import unittest
from src.live_operating_console import LiveOperatingConsole
from src.live_runtime_bridge import LiveRuntimeBridge
from src.standardization_engine import OperatingStandard

class LiveRuntimeStandardEnforcementTests(unittest.TestCase):
    def test_compliant_standard_reaches_runtime(self):
        console=LiveOperatingConsole("2026-10-05","Execute governed command")
        console.add_command("cmd:1","P1","Execute governed command","system","runtime response")
        standard=OperatingStandard("std:a:v1","a","Require evidence","Higher quality",1,"ACTIVE")
        record=LiveRuntimeBridge(console).execute("cmd:1",standard=standard,applied_rule="Require evidence")
        self.assertEqual(record.final_status,"LEARNED")

    def test_noncompliant_standard_blocks_before_runtime(self):
        console=LiveOperatingConsole("2026-10-05","Execute governed command")
        console.add_command("cmd:2","P1","Execute governed command","system","runtime response")
        standard=OperatingStandard("std:a:v1","a","Require evidence","Higher quality",1,"ACTIVE")
        with self.assertRaises(PermissionError):
            LiveRuntimeBridge(console).execute("cmd:2",standard=standard,applied_rule="Skip evidence")
        self.assertEqual(console.snapshot().commands[0].status,"INBOX")

if __name__ == "__main__": unittest.main()
