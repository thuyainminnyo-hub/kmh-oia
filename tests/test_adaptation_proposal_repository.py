import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Barrier

from src.adaptation_engine import AdaptationEngine
from src.adaptation_proposal_repository import (
    AdaptationProposalConflict,
    SQLiteAdaptationProposalRepository,
)
from src.operating_memory import OperatingMemoryRecord


class AdaptationProposalRepositoryTests(unittest.TestCase):
    def setUp(self):
        self.record = OperatingMemoryRecord(
            command_id="cmd:1",
            timestamp="2026-10-27T00:00:00+00:00",
            wanted="wanted",
            did="did",
            actual="actual",
            verified="verified",
            decision="decision",
            learned="learned",
            changed="changed",
            next_command="next",
            confidence=0.8,
            event_id="learning:event-1",
        )
        self.kwargs = dict(
            pattern="quality",
            problem="poor outcome",
            proposed_change="review rule",
            expected_effect="improve outcome",
            next_experiment="shadow test",
        )

    def test_in_memory_database_is_rejected_because_connections_are_independent(self):
        with self.assertRaisesRegex(ValueError, "file-backed database"):
            SQLiteAdaptationProposalRepository(":memory:")

    def test_proposal_is_durable_across_repository_recreation(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = str(Path(tmp) / "proposals.sqlite3")
            first = AdaptationEngine(SQLiteAdaptationProposalRepository(path)).propose(
                self.record, **self.kwargs
            )
            recreated = AdaptationEngine(SQLiteAdaptationProposalRepository(path)).propose(
                self.record, **self.kwargs
            )
            self.assertEqual(first.id, recreated.id)
            self.assertEqual(first, recreated)

    def test_replay_preserves_governance_status_after_restart(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = str(Path(tmp) / "proposals.sqlite3")
            engine = AdaptationEngine(SQLiteAdaptationProposalRepository(path))
            proposal = engine.propose(self.record, **self.kwargs)
            approved = engine.approve(proposal)
            replayed = AdaptationEngine(SQLiteAdaptationProposalRepository(path)).propose(
                self.record, **self.kwargs
            )
            self.assertEqual(approved.status, "APPROVED")
            self.assertEqual(replayed.status, "APPROVED")

    def test_conflicting_payload_for_same_event_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = str(Path(tmp) / "proposals.sqlite3")
            engine = AdaptationEngine(SQLiteAdaptationProposalRepository(path))
            engine.propose(self.record, **self.kwargs)
            changed = dict(self.kwargs, problem="different problem")
            with self.assertRaises(AdaptationProposalConflict):
                engine.propose(self.record, **changed)

    def test_concurrent_workers_create_one_canonical_proposal(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = str(Path(tmp) / "proposals.sqlite3")
            SQLiteAdaptationProposalRepository(path)

            def create(_):
                engine = AdaptationEngine(SQLiteAdaptationProposalRepository(path))
                return engine.propose(self.record, **self.kwargs)

            with ThreadPoolExecutor(max_workers=8) as pool:
                proposals = list(pool.map(create, range(16)))
            self.assertEqual(len({proposal.id for proposal in proposals}), 1)
            self.assertTrue(
                SQLiteAdaptationProposalRepository(path).health_check()
            )

    def test_competing_approve_and_reject_allow_exactly_one_transition(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = str(Path(tmp) / "proposals.sqlite3")
            initial = AdaptationEngine(SQLiteAdaptationProposalRepository(path)).propose(
                self.record, **self.kwargs
            )
            ready = Barrier(2)

            def transition(action):
                engine = AdaptationEngine(SQLiteAdaptationProposalRepository(path))
                ready.wait()
                try:
                    return ("won", getattr(engine, action)(initial).status)
                except ValueError:
                    return ("lost", action)

            with ThreadPoolExecutor(max_workers=2) as pool:
                results = list(pool.map(transition, ("approve", "reject")))

            self.assertEqual(sum(result[0] == "won" for result in results), 1)
            self.assertEqual(sum(result[0] == "lost" for result in results), 1)
            stored = SQLiteAdaptationProposalRepository(path).get(initial.id)
            self.assertIn(stored["status"], {"APPROVED", "REJECTED"})
            winner = next(result[1] for result in results if result[0] == "won")
            self.assertEqual(stored["status"], winner)

    def test_proposed_status_cannot_be_written_as_a_noop_transition(self):
        with tempfile.TemporaryDirectory() as tmp:
            repository = SQLiteAdaptationProposalRepository(
                str(Path(tmp) / "proposals.sqlite3")
            )
            engine = AdaptationEngine(repository)
            proposal = engine.propose(self.record, **self.kwargs)
            with self.assertRaisesRegex(ValueError, "unsupported or non-transition"):
                repository.update_status(proposal.id, "PROPOSED")

    def test_status_transition_is_durable_and_cannot_be_repeated(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = str(Path(tmp) / "proposals.sqlite3")
            engine = AdaptationEngine(SQLiteAdaptationProposalRepository(path))
            proposal = engine.propose(self.record, **self.kwargs)
            approved = engine.approve(proposal)
            with self.assertRaisesRegex(ValueError, "only proposed adaptations"):
                engine.approve(approved)
            applied = engine.apply(approved)
            replayed = AdaptationEngine(SQLiteAdaptationProposalRepository(path)).propose(
                self.record, **self.kwargs
            )
            self.assertEqual(applied.status, "APPLIED")
            self.assertEqual(replayed.status, "APPLIED")


if __name__ == "__main__":
    unittest.main()
