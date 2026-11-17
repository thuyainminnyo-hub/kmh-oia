import tempfile
import unittest
from pathlib import Path

from src.trust_assurance import (
    AuditCheckpointAuthority,
    record_authenticated_qa_decision,
    IndependentCheckpointStore,
    ReviewerReplayStore,
    ReviewerTokenAuthority,
)


class ReviewerTrustTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        self.replay = ReviewerReplayStore(root / "reviewer-replay.sqlite")
        self.authority = ReviewerTokenAuthority(
            key_id="reviewer-key-v1", key=b"r" * 32,
            issuer="kmh-oia-test-issuer", audience="kmh-oia-qa",
        )

    def test_valid_reviewer_assertion_authenticates_subject_and_role(self):
        token = self.authority.issue(subject="reviewer-1", roles=["qa_approver"], now=100)
        principal = self.authority.verify(token, required_role="qa_approver",
                                          replay_store=self.replay, now=101)
        self.assertEqual(principal.subject, "reviewer-1")
        self.assertIn("qa_approver", principal.roles)

    def test_tampered_token_is_rejected(self):
        token = self.authority.issue(subject="reviewer-1", roles=["qa_approver"], now=100)
        payload, signature = token.split(".")
        forged = payload[:-2] + ("00" if payload[-2:] != "00" else "11") + "." + signature
        with self.assertRaisesRegex(ValueError, "invalid reviewer assertion"):
            self.authority.verify(forged, required_role="qa_approver",
                                  replay_store=self.replay, now=101)

    def test_expired_assertion_is_rejected(self):
        token = self.authority.issue(subject="reviewer-1", roles=["qa_approver"],
                                     ttl_seconds=10, now=100)
        with self.assertRaisesRegex(ValueError, "expired"):
            self.authority.verify(token, required_role="qa_approver",
                                  replay_store=self.replay, now=110)

    def test_future_dated_assertion_is_rejected(self):
        token = self.authority.issue(subject="reviewer-1", roles=["qa_approver"], now=110)
        with self.assertRaisesRegex(ValueError, "expired"):
            self.authority.verify(token, required_role="qa_approver",
                                  replay_store=self.replay, now=100)

    def test_wrong_role_is_rejected(self):
        token = self.authority.issue(subject="reviewer-1", roles=["qa_viewer"], now=100)
        with self.assertRaisesRegex(ValueError, "not authorized"):
            self.authority.verify(token, required_role="qa_approver",
                                  replay_store=self.replay, now=101)

    def test_replay_is_rejected(self):
        token = self.authority.issue(subject="reviewer-1", roles=["qa_approver"],
                                     now=100, nonce="fixed-nonce")
        self.authority.verify(token, required_role="qa_approver",
                              replay_store=self.replay, now=101)
        with self.assertRaisesRegex(ValueError, "replay"):
            self.authority.verify(token, required_role="qa_approver",
                                  replay_store=self.replay, now=101)

    def test_wrong_audience_and_issuer_are_rejected(self):
        other = ReviewerTokenAuthority(key_id="reviewer-key-v1", key=b"r" * 32,
                                       issuer="other-issuer", audience="other-audience")
        token = other.issue(subject="reviewer-1", roles=["qa_approver"], now=100)
        with self.assertRaisesRegex(ValueError, "issuer or audience"):
            self.authority.verify(token, required_role="qa_approver",
                                  replay_store=self.replay, now=101)


    def test_authenticated_qa_decision_uses_verified_subject_not_caller_claim(self):
        class Sink:
            def record_qa_decision(self, **kwargs):
                return kwargs

        token = self.authority.issue(subject="verified-reviewer", roles=["qa_approver"], now=100)
        result = record_authenticated_qa_decision(
            audit_sink=Sink(), authority=self.authority, replay_store=self.replay,
            reviewer_token=token, job_id="job-1", output_sha256="a" * 64,
            decision="approved", now=101,
        )
        self.assertEqual(result["reviewer_id"], "verified-reviewer")

    def test_authenticated_qa_decision_rejects_forged_reviewer_before_sink(self):
        class Sink:
            called = False
            def record_qa_decision(self, **kwargs):
                self.called = True
                return kwargs

        sink = Sink()
        with self.assertRaisesRegex(ValueError, "invalid reviewer assertion"):
            record_authenticated_qa_decision(
                audit_sink=sink, authority=self.authority, replay_store=self.replay,
                reviewer_token="forged", job_id="job-1", output_sha256="a" * 64,
                decision="approved", now=101,
            )
        self.assertFalse(sink.called)

    def test_weak_keys_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "32 bytes"):
            ReviewerTokenAuthority(key_id="weak", key=b"short",
                                   issuer="issuer", audience="audience")


class AuditCheckpointTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.store = IndependentCheckpointStore(Path(self.temp.name) / "independent" / "trust.sqlite")
        self.authority = AuditCheckpointAuthority(key_id="audit-key-v1", key=b"a" * 32)

    def test_checkpoint_round_trip_and_independent_head_verification(self):
        events = [{"event_hash": "1" * 64}, {"event_hash": "2" * 64}]
        checkpoint = self.authority.create(events, self.store, now=200)
        self.assertEqual(checkpoint.sequence, 1)\n        self.assertEqual(checkpoint.event_count, 2)
        self.assertTrue(self.authority.verify(events, self.store))

    def test_rewritten_chain_head_is_detected(self):
        events = [{"event_hash": "1" * 64}]
        self.authority.create(events, self.store, now=200)
        rewritten = [{"event_hash": "f" * 64}]
        self.assertFalse(self.authority.verify(rewritten, self.store))

    def test_truncated_chain_is_detected(self):
        events = [{"event_hash": "1" * 64}, {"event_hash": "2" * 64}]
        self.authority.create(events, self.store, now=200)
        self.assertFalse(self.authority.verify(events[:1], self.store))

    def test_empty_chain_cannot_be_checkpointed(self):
        with self.assertRaisesRegex(ValueError, "empty"):
            self.authority.create([], self.store, now=200)

    def test_checkpoint_sequence_must_advance_by_one_event(self):
        self.authority.create([{"event_hash": "1" * 64}], self.store, now=200)
        with self.assertRaisesRegex(ValueError, "sequence"):
            self.authority.create([{"event_hash": "1" * 64}, {"event_hash": "2" * 64},
                                   {"event_hash": "3" * 64}], self.store, now=201)

    def test_missing_checkpoint_fails_closed(self):
        self.assertFalse(self.authority.verify([{"event_hash": "1" * 64}], self.store))

    def test_checkpoint_signature_tampering_is_detected(self):
        events = [{"event_hash": "1" * 64}]
        self.authority.create(events, self.store, now=200)
        with __import__("sqlite3").connect(self.store.path) as db:
            db.execute("UPDATE audit_checkpoints SET signature = ?", ("0" * 64,))
        self.assertFalse(self.authority.verify(events, self.store))

    def test_checkpoint_store_health_check(self):
        self.assertTrue(self.store.health_check())
        with __import__("sqlite3").connect(self.store.path) as db:
            db.execute("DROP TABLE audit_checkpoints")
        self.assertFalse(self.store.health_check())


if __name__ == "__main__":
    unittest.main()
