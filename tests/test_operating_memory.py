from concurrent.futures import ThreadPoolExecutor
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

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

    def test_duplicate_event_id_returns_original_record_and_survives_restart(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "memory.json"
            memory = OperatingMemory(path)
            kwargs = dict(
                command_id="cmd-duplicate",
                wanted="w", did="d", actual="a", verified="v",
                decision="decision", learned="learned", changed="changed",
                next_command="next", event_id="learning:event-1",
            )
            first = memory.record(**kwargs)
            duplicate = memory.record(**kwargs)
            whitespace_duplicate = memory.record(**{**kwargs, "event_id": " learning:event-1 "})
            self.assertEqual(duplicate, first)
            self.assertEqual(whitespace_duplicate, first)
            self.assertEqual(len(memory.recent(10)), 1)

            restored = OperatingMemory(path)
            self.assertEqual(restored.record(**kwargs), first)
            self.assertEqual(len(restored.recent(10)), 1)

    def test_concurrent_duplicate_event_id_is_recorded_once(self) -> None:
        memory = OperatingMemory()
        kwargs = dict(
            command_id="cmd-concurrent",
            wanted="w", did="d", actual="a", verified="v",
            decision="decision", learned="learned", changed="changed",
            next_command="next", event_id="learning:concurrent-1",
        )
        with ThreadPoolExecutor(max_workers=12) as executor:
            records = list(executor.map(lambda _: memory.record(**kwargs), range(40)))

        self.assertTrue(all(record == records[0] for record in records))
        self.assertEqual(len(memory.recent(10)), 1)

    def test_persist_failure_rolls_back_record_and_allows_retry(self) -> None:
        memory = OperatingMemory()
        kwargs = dict(
            command_id="cmd-retry",
            wanted="w", did="d", actual="a", verified="v",
            decision="decision", learned="learned", changed="changed",
            next_command="next", event_id="learning:retry-1",
        )
        with patch.object(memory, "_persist", side_effect=OSError("simulated disk failure")):
            with self.assertRaisesRegex(OSError, "simulated disk failure"):
                memory.record(**kwargs)
        self.assertEqual(memory.recent(10), ())

        record = memory.record(**kwargs)
        self.assertEqual(memory.recent(1), (record,))
        self.assertEqual(memory.record(**kwargs), record)
        self.assertEqual(len(memory.recent(10)), 1)

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
