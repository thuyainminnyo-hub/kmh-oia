import hashlib
import json
import tempfile
import time
import unittest
from pathlib import Path


def make_events(payloads):
    events = []
    previous = "0" * 64
    for index, payload in enumerate(payloads):
        event = {"event_type": "test", "job_id": f"job-{index}", "payload": payload,
                 "previous_hash": previous}
        canonical = json.dumps(event, sort_keys=True, separators=(",", ":"))
        event["event_hash"] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
        previous = event["event_hash"]
        events.append(event)
    return events


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
                principal = kwargs["reviewer_authority"].verify(
                    kwargs["reviewer_token"], required_role=kwargs["required_role"],
                    replay_store=kwargs["reviewer_replay_store"], now=kwargs.get("now"),
                )
                return {"reviewer_id": principal.subject}

        current = int(time.time())
        token = self.authority.issue(subject="verified-reviewer", roles=["qa_approver"], now=current)
        result = record_authenticated_qa_decision(
            audit_sink=Sink(), authority=self.authority, replay_store=self.replay,
            reviewer_token=token, job_id="job-1", output_sha256="a" * 64,
            decision="approved", now=current,
        )
        self.assertEqual(result["reviewer_id"], "verified-reviewer")

    def test_authenticated_qa_decision_rejects_forged_reviewer_before_sink(self):
        class Sink:
            appended = False
            def record_qa_decision(self, **kwargs):
                principal = kwargs["reviewer_authority"].verify(
                    kwargs["reviewer_token"], required_role=kwargs["required_role"],
                    replay_store=kwargs["reviewer_replay_store"],
                )
                self.appended = True
                return {"reviewer_id": principal.subject}

        sink = Sink()
        with self.assertRaisesRegex(ValueError, "invalid reviewer assertion"):
            record_authenticated_qa_decision(
                audit_sink=sink, authority=self.authority, replay_store=self.replay,
                reviewer_token="forged", job_id="job-1", output_sha256="a" * 64,
                decision="approved", now=101,
            )
        self.assertFalse(sink.appended)

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
        events = make_events([{"n": 1}, {"n": 2}])
        checkpoint = self.authority.create(events, self.store, now=200)
        self.assertEqual(checkpoint.sequence, 1)
        self.assertEqual(checkpoint.event_count, 2)
        self.assertTrue(self.authority.verify(events, self.store))

    def test_rewritten_chain_head_is_detected(self):
        events = make_events([{"n": 1}])
        self.authority.create(events, self.store, now=200)
        rewritten = make_events([{"n": "rewritten"}])
        self.assertFalse(self.authority.verify(rewritten, self.store))

    def test_truncated_chain_is_detected(self):
        events = make_events([{"n": 1}, {"n": 2}])
        self.authority.create(events, self.store, now=200)
        self.assertFalse(self.authority.verify(events[:1], self.store))

    def test_empty_chain_cannot_be_checkpointed(self):
        with self.assertRaisesRegex(ValueError, "empty"):
            self.authority.create([], self.store, now=200)

    def test_checkpoint_sequence_advances_when_audit_event_count_advances(self):
        first = self.authority.create(make_events([{"n": 1}]), self.store, now=200)
        second = self.authority.create(make_events([{"n": 1}, {"n": 2}]), self.store, now=201)
        self.assertEqual((first.sequence, first.event_count), (1, 1))
        self.assertEqual((second.sequence, second.event_count), (2, 2))

    def test_checkpoint_rejects_no_new_audit_events(self):
        events = make_events([{"n": 1}])
        self.authority.create(events, self.store, now=200)
        with self.assertRaisesRegex(ValueError, "event count"):
            self.authority.create(events, self.store, now=201)


    def test_checkpoint_rejects_event_with_forged_hash(self):
        events = make_events([{"n": 1}, {"n": 2}])
        events[0]["payload"] = {"n": "tampered"}
        with self.assertRaisesRegex(ValueError, "invalid or unverified"):
            self.authority.create(events, self.store, now=200)

    def test_checkpoint_rejects_broken_previous_hash_link(self):
        events = make_events([{"n": 1}, {"n": 2}])
        events[1]["previous_hash"] = "f" * 64
        canonical = json.dumps({k: v for k, v in events[1].items() if k != "event_hash"},
                               sort_keys=True, separators=(",", ":"))
        events[1]["event_hash"] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
        with self.assertRaisesRegex(ValueError, "invalid or unverified"):
            self.authority.create(events, self.store, now=200)

    def test_verify_rejects_tampered_middle_event_even_if_final_head_is_unchanged(self):
        events = make_events([{"n": 1}, {"n": 2}, {"n": 3}])
        self.authority.create(events, self.store, now=200)
        altered = [dict(event) for event in events]
        altered[0]["payload"] = {"n": "altered"}
        self.assertFalse(self.authority.verify(altered, self.store))

    def test_missing_checkpoint_fails_closed(self):
        self.assertFalse(self.authority.verify(make_events([{"n": 1}]), self.store))

    def test_checkpoint_signature_tampering_is_detected(self):
        events = make_events([{"n": 1}])
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
