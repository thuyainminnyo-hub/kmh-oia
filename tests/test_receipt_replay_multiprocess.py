"""Cross-process race regression for the SQLite receipt replay guard.

This proves only local processes sharing one SQLite file; it is not evidence
for separate hosts, network filesystems, or a production deployment.
"""
import multiprocessing
import tempfile
import unittest
from pathlib import Path

from src.receipt_replay_store import SQLiteReceiptReplayStore


def _claim_after_barrier(db_path: str, barrier, results) -> None:
    store = SQLiteReceiptReplayStore(db_path)
    barrier.wait(timeout=15)
    claim = store.claim("race-test-provider", "same-record", "same-content-hash")
    results.put({"accepted": claim.accepted, "reason": claim.reason})


class SQLiteMultiprocessReplayRaceTests(unittest.TestCase):
    def test_only_one_independent_process_wins_same_replay_claim(self):
        process_count = 8
        with tempfile.TemporaryDirectory() as tmp:
            db_path = str(Path(tmp) / "shared-replay.sqlite3")
            SQLiteReceiptReplayStore(db_path)  # initialize before child processes start

            context = multiprocessing.get_context("spawn")
            barrier = context.Barrier(process_count)
            results = context.Queue()
            processes = [
                context.Process(target=_claim_after_barrier, args=(db_path, barrier, results))
                for _ in range(process_count)
            ]

            try:
                for process in processes:
                    process.start()

                outcomes = [results.get(timeout=25) for _ in range(process_count)]
                for process in processes:
                    process.join(timeout=25)

                self.assertTrue(
                    all(process.exitcode == 0 for process in processes),
                    f"child process exit codes: {[process.exitcode for process in processes]}",
                )
                self.assertEqual(
                    sum(outcome["accepted"] is True for outcome in outcomes),
                    1,
                    f"expected exactly one accepted claim, got {outcomes!r}",
                )
                rejected = [outcome for outcome in outcomes if outcome["accepted"] is False]
                self.assertEqual(len(rejected), process_count - 1)
                self.assertTrue(
                    all("replay" in outcome["reason"].lower() for outcome in rejected),
                    f"all losing claims should be explicit replay rejections: {rejected!r}",
                )
            finally:
                for process in processes:
                    if process.is_alive():
                        process.terminate()
                    process.join(timeout=5)
                results.close()
                results.join_thread()


if __name__ == "__main__":
    unittest.main()
