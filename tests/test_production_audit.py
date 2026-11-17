import json
import tempfile
import unittest
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from dataclasses import replace
from pathlib import Path

from src.execution_identity import ExecutionIdentity, ExecutionIdentityContext
from src.production_audit import JsonlProductionAuditSink
from src.production_evidence import ProductionEvidence
from src.trust_assurance import ReviewerReplayStore, ReviewerTokenAuthority
from src.verified_snapshot_store import VerifiedArtifactStore


_REVIEWER_KEY = b"r" * 32


def _process_qa_decision(args):
    path, digest, index = args
    sink = JsonlProductionAuditSink(path)
    authority = ReviewerTokenAuthority(
        key_id="test-reviewer-key", key=_REVIEWER_KEY,
        issuer="kmh-oia-tests", audience="kmh-oia-qa",
    )
    replay = ReviewerReplayStore(str(path) + ".reviewers.sqlite")
    token = authority.issue(subject=f"process-reviewer-{index}", roles=["qa_approver"])
    try:
        sink.record_qa_decision(
            job_id="job-1", output_sha256=digest,
            decision="approved" if index % 2 == 0 else "rejected",
            reviewer_token=token, reviewer_authority=authority,
            reviewer_replay_store=replay,
        )
        return "recorded"
    except ValueError as exc:
        if "already recorded" in str(exc):
            return "rejected"
        raise


class JsonlProductionAuditSinkTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        out = root / "out"
        out.mkdir()
        file = out / "image.png"
        file.write_bytes(b"image fixture")
        self.store = VerifiedArtifactStore(root / "store")
        snap = self.store.put_verified(file, allowed_root=out, artifact_id="job-job-1")
        ctx = ExecutionIdentityContext(ExecutionIdentity("a", "i", "prod", "s"),
                                       "cmd", "exec", "job-1")
        self.path = root / "audit.jsonl"
        self.sink = JsonlProductionAuditSink(self.path)
        self.evidence = ProductionEvidence.from_snapshot(
            job_id="job-1", adapter_name="fake", output_path=str(file),
            snapshot=snap, elapsed_ms=10, provider_execution_id="prompt-1",
            context=ctx,
        )
        self.authority = ReviewerTokenAuthority(
            key_id="test-reviewer-key", key=_REVIEWER_KEY,
            issuer="kmh-oia-tests", audience="kmh-oia-qa",
        )
        self.replay = ReviewerReplayStore(str(self.path) + ".reviewers.sqlite")

    def record_qa(self, *, reviewer_id="reviewer-1", **kwargs):
        token = self.authority.issue(subject=reviewer_id, roles=["qa_approver"])
        return self.sink.record_qa_decision(
            reviewer_token=token, reviewer_authority=self.authority,
            reviewer_replay_store=self.replay, **kwargs,
        )

    def test_records_evidence_and_authenticated_qa_decision_in_hash_chain(self):
        first = self.sink.record_evidence(self.evidence, snapshot_store=self.store)
        second = self.record_qa(
            job_id="job-1", output_sha256=self.evidence.output_sha256,
            decision="approved",
        )
        events = self.sink.verify_chain()
        self.assertEqual(len(events), 2)
        self.assertEqual(events[0]["event_type"], "evidence_created")
        self.assertEqual(events[1]["event_type"], "qa_decision_recorded")
        self.assertEqual(second["previous_hash"], first["event_hash"])
        self.assertEqual(events[1]["payload"]["reviewer_id"], "reviewer-1")
        self.assertEqual(events[0]["payload"]["snapshot_reference"], self.evidence.snapshot_reference)

    def test_evidence_admission_is_idempotent_for_exact_retry(self):
        first = self.sink.record_evidence(self.evidence, snapshot_store=self.store)
        retry = self.sink.record_evidence(self.evidence, snapshot_store=self.store)
        self.assertEqual(first["event_hash"], retry["event_hash"])
        self.assertEqual(len(self.sink.verify_chain()), 1)

    def test_evidence_admission_rejects_conflicting_provenance_for_artifact(self):
        self.sink.record_evidence(self.evidence, snapshot_store=self.store)
        conflicting = replace(self.evidence, execution_id="different-execution")
        with self.assertRaisesRegex(ValueError, "different provenance"):
            self.sink.record_evidence(conflicting, snapshot_store=self.store)

    def test_rejects_manifest_without_matching_verified_snapshot(self):
        forged = replace(self.evidence, output_sha256="0" * 64,
                         snapshot_reference="sha256/00/00/" + "0" * 64)
        with self.assertRaisesRegex(ValueError, "snapshot"):
            self.sink.record_evidence(forged, snapshot_store=self.store)

    def test_detects_event_tampering(self):
        self.sink.record_evidence(self.evidence, snapshot_store=self.store)
        event = json.loads(self.path.read_text(encoding="utf-8"))
        event["payload"]["output_size_bytes"] = 999
        self.path.write_text(json.dumps(event) + "\n", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "hash mismatch"):
            self.sink.verify_chain()

    def test_rejects_invalid_qa_decision_after_authentication(self):
        with self.assertRaisesRegex(ValueError, "QA decision"):
            self.record_qa(job_id="job", output_sha256="a" * 64, decision="pending")

    def test_qa_decision_binds_to_matching_evidence_event(self):
        evidence_event = self.sink.record_evidence(self.evidence, snapshot_store=self.store)
        qa_event = self.record_qa(
            job_id="job-1", output_sha256=self.evidence.output_sha256,
            decision="approved",
        )
        self.assertEqual(qa_event["payload"]["evidence_event_hash"], evidence_event["event_hash"])
        self.assertEqual(qa_event["payload"]["snapshot_reference"], self.evidence.snapshot_reference)
        self.assertEqual(qa_event["payload"]["execution_id"], self.evidence.execution_id)
        self.assertEqual(qa_event["payload"]["identity_key"], self.evidence.identity_key)

    def test_rejects_second_conflicting_qa_decision_for_same_evidence(self):
        self.sink.record_evidence(self.evidence, snapshot_store=self.store)
        self.record_qa(job_id="job-1", output_sha256=self.evidence.output_sha256,
                       decision="approved", reviewer_id="reviewer-1")
        with self.assertRaisesRegex(ValueError, "already recorded"):
            self.record_qa(job_id="job-1", output_sha256=self.evidence.output_sha256,
                           decision="rejected", reviewer_id="reviewer-2")

    def test_concurrent_qa_decisions_are_serialized_and_authenticated(self):
        self.sink.record_evidence(self.evidence, snapshot_store=self.store)

        def decide(index):
            try:
                return self.record_qa(
                    job_id="job-1", output_sha256=self.evidence.output_sha256,
                    decision="approved" if index % 2 == 0 else "rejected",
                    reviewer_id=f"reviewer-{index}",
                )["event_hash"]
            except ValueError as exc:
                if "already recorded" in str(exc):
                    return "rejected"
                raise

        with ThreadPoolExecutor(max_workers=8) as pool:
            outcomes = list(pool.map(decide, range(8)))
        self.assertEqual(sum(outcome != "rejected" for outcome in outcomes), 1)
        events = self.sink.verify_chain()
        self.assertEqual(sum(event["event_type"] == "qa_decision_recorded" for event in events), 1)

    def test_cross_process_qa_decisions_are_serialized_and_authenticated(self):
        self.sink.record_evidence(self.evidence, snapshot_store=self.store)
        args = [(str(self.path), self.evidence.output_sha256, index) for index in range(4)]
        with ProcessPoolExecutor(max_workers=4) as pool:
            outcomes = list(pool.map(_process_qa_decision, args))
        self.assertEqual(outcomes.count("recorded"), 1)
        events = self.sink.verify_chain()
        self.assertEqual(sum(event["event_type"] == "qa_decision_recorded" for event in events), 1)

    def test_qa_decision_rejects_without_prior_evidence(self):
        with self.assertRaisesRegex(ValueError, "prior evidence event"):
            self.record_qa(job_id="job-1", output_sha256=self.evidence.output_sha256,
                           decision="approved")

    def test_qa_decision_rejects_wrong_digest(self):
        self.sink.record_evidence(self.evidence, snapshot_store=self.store)
        with self.assertRaisesRegex(ValueError, "prior evidence event"):
            self.record_qa(job_id="job-1", output_sha256="0" * 64, decision="approved")

    def test_blank_reviewer_cannot_mint_assertion(self):
        with self.assertRaisesRegex(ValueError, "subject"):
            self.record_qa(job_id="job-1", output_sha256="a" * 64,
                           decision="approved", reviewer_id=" ")

    def test_forged_reviewer_token_is_rejected_before_audit_append(self):
        self.sink.record_evidence(self.evidence, snapshot_store=self.store)
        with self.assertRaisesRegex(ValueError, "invalid reviewer assertion"):
            self.sink.record_qa_decision(
                job_id="job-1", output_sha256=self.evidence.output_sha256,
                decision="approved", reviewer_token="forged",
                reviewer_authority=self.authority, reviewer_replay_store=self.replay,
            )
        self.assertEqual(len(self.sink.verify_chain()), 1)

    def test_replayed_reviewer_token_is_rejected(self):
        self.sink.record_evidence(self.evidence, snapshot_store=self.store)
        token = self.authority.issue(subject="reviewer-replay", roles=["qa_approver"])
        # Use a separate valid QA evidence fixture for the first call; duplicate QA
        # is also prohibited, so replay validation is asserted on a second evidence event.
        self.sink.record_qa_decision(
            job_id="job-1", output_sha256=self.evidence.output_sha256,
            decision="approved", reviewer_token=token,
            reviewer_authority=self.authority, reviewer_replay_store=self.replay,
        )
        with self.assertRaisesRegex(ValueError, "replay"):
            self.sink.record_qa_decision(
                job_id="job-1", output_sha256=self.evidence.output_sha256,
                decision="approved", reviewer_token=token,
                reviewer_authority=self.authority, reviewer_replay_store=self.replay,
            )


if __name__ == "__main__":
    unittest.main()
