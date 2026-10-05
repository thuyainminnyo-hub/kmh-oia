import tempfile
import unittest
from pathlib import Path

from src.operating_memory import OperatingMemory


class OperatingMemoryTests(unittest.TestCase):
    def test_records_execution_chain_and_persists(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "memory.json"
            memory = OperatingMemory(path)
            record = memory.record(
                command_id="cmd-1",
                wanted="Ship verified execution",
                did="Ran command through OIA runtime",
                actual="Runtime returned a governed response",
                verified="Trace and evaluation passed",
                decision="Keep evidence-first verification",
                learned="Trace-backed execution is auditable",
                changed="Require trace evidence for verification",
                next_command="Apply evidence rule to next workflow",
            )
            self.assertEqual(memory.recent(1)[0], record)

            restored = OperatingMemory(path)
            self.assertEqual(restored.recent(1)[0], record)
            self.assertEqual(len(restored.search("evidence")), 1)

    def test_rejects_invalid_confidence(self) -> None:
        memory = OperatingMemory()
        with self.assertRaises(ValueError):
            memory.record(
                command_id="cmd-1",
                wanted="x",
                did="x",
                actual="x",
                verified="x",
                decision="x",
                learned="x",
                changed="x",
                next_command="x",
                confidence=1.5,
            )


if __name__ == "__main__":
    unittest.main()
