"""Composed trusted decision -> runtime execution -> learning admission integration test.

The deterministic adapter validates application wiring and attribution only. It
is not evidence of real-provider authenticity or production deployment.
"""
from datetime import datetime, timezone
from dataclasses import replace
from pathlib import Path
import tempfile
import unittest

from src.decision_queue import DecisionItem
from src.live_operating_console import LiveOperatingConsole
from src.trusted_decision_learning_service import TrustedOutcomeClassification
from src.trusted_learning_runtime import (
    TrustedLearningRuntimeConfig,
    build_trusted_learning_runtime,
)
from src.trusted_source_receipt import TrustedSourceReceipt


class DeterministicReceiptAdapter:
    provider_name = "booking-provider"

    def __init__(self):
        self.raw_observation = "booking outcome=failed"
        self.authentic = True

    def fetch_receipt(self, source_record_id, execution_id):
        return TrustedSourceReceipt(
            provider_name=self.provider_name,
            source_record_id=source_record_id,
            execution_id=execution_id,
            raw_observation=self.raw_observation,
            observed_at=datetime.now(timezone.utc).isoformat(),
            content_hash="sha256:e2e-receipt-stable",
            verification_method="deterministic-test-adapter",
        )

    def verify_receipt(self, receipt):
        return (
            receipt.provider_name == self.provider_name
            and receipt.content_hash == "sha256:e2e-receipt-stable"
            and self.authentic
        )

    def match_execution(self, receipt, execution_id):
        return receipt.execution_id == execution_id


class FailedOutcomeClassifier:
    def __init__(self):
        self.fail = False

    def classify(self, decision, execution, receipt):
        if self.fail:
            raise RuntimeError("simulated classifier outage")
        assert decision.id == execution.source_decision_id
        assert receipt.execution_id == execution.operating_loop.execution_id
        return TrustedOutcomeClassification(
            outcome_positive=False,
            reason="The deterministic test receipt reports a failed booking.",
            evidence_id="evidence:e2e-1",
        )


class TrustedDecisionLearningRuntimeIntegrationTests(unittest.TestCase):
    def test_approved_decision_executes_and_is_admitted_by_composed_learning_service(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            decision = DecisionItem(
                id="decision:e2e-1",
                signal_kind="QUALITY_RISK",
                severity="HIGH",
                problem="Verify booking outcome",
                recommended_action="Execute a bounded verification command",
                owner="test-owner",
                status="APPROVED",
            )
            console = LiveOperatingConsole(
                date="2026-10-28",
                primary_objective="Trusted decision to learning integration test",
            )
            command = console.add_command(
                "cmd:e2e-1",
                objective="Verify a deterministic booking outcome",
                priority="P1",
                owner="test-owner",
                expected_output="A runtime execution with linked trusted receipt",
                source_decision_id=decision.id,
                next_action="Review the governed adaptation proposal",
            )
            runtime = build_trusted_learning_runtime(
                console=console,
                config=TrustedLearningRuntimeConfig(
                    memory_path=str(root / "memory.json"),
                    proposal_sqlite_path=str(root / "proposals.sqlite3"),
                    replay_sqlite_path=str(root / "replay.sqlite3"),
                    allowed_source_providers=("booking-provider",),
                ),
                trusted_source_adapter=DeterministicReceiptAdapter(),
                classifier=FailedOutcomeClassifier(),
            )

            execution = runtime.bridge.execute(
                command.id,
                source_record_id="record:e2e-1",
                verification_status="OUTCOME_LINKED",
                outcome_linked=True,
            )

            self.assertEqual(execution.source_decision_id, decision.id)
            self.assertEqual(execution.command_id, command.id)
            self.assertIsNotNone(execution.operating_loop)
            execution_id = execution.operating_loop.execution_id
            self.assertTrue(execution_id)
            self.assertTrue(execution.admission.learning_admitted)
            self.assertEqual(execution.admission.evidence_status, "OUTCOME_LINKED")
            self.assertTrue(execution.trusted_receipt_verification.verified)
            self.assertEqual(execution.trusted_receipt_verification.provider_name, "booking-provider")
            self.assertEqual(execution.trusted_receipt_verification.execution_id, execution_id)
            self.assertEqual(execution.trusted_receipt_verification.source_record_id, "record:e2e-1")
            self.assertEqual(
                execution.trusted_receipt_verification.content_hash,
                "sha256:e2e-receipt-stable",
            )
            self.assertEqual(
                execution.trusted_receipt_verification.raw_observation,
                "booking outcome=failed",
            )
            self.assertEqual(
                execution.trusted_receipt_verification.verification_method,
                "deterministic-test-adapter",
            )

            # Pass the bridge-produced execution record directly to the learning gate.
            learning_execution = execution
            result = runtime.learning_service.capture_execution(
                decision,
                learning_execution,
                evidence_id="evidence:e2e-1",
                policy_version="policy:e2e-v1",
                next_command="Review the proposed adaptation",
            )

            self.assertTrue(result.admitted, result.reasons)
            self.assertEqual(result.execution_id, execution_id)
            self.assertEqual(result.memory.event_id, result.adaptation.id.removeprefix("adapt:"))
            self.assertEqual(result.adaptation.status, "PROPOSED")
            stored_proposal = runtime.proposal_repository.get(result.adaptation.id)
            self.assertIsNotNone(stored_proposal)
            self.assertEqual(stored_proposal["status"], "PROPOSED")
            self.assertEqual(stored_proposal["id"], result.adaptation.id)
            self.assertTrue(runtime.replay_store.health_check())

            # Retrying the same admitted decision/execution/evidence must reuse the
            # deterministic learning event and durable proposal, without duplicates.
            memory_count_before_retry = len(runtime.memory.recent(20))
            retry = runtime.learning_service.capture_execution(
                decision,
                learning_execution,
                evidence_id="evidence:e2e-1",
                policy_version="policy:e2e-v1",
                next_command="Review the proposed adaptation",
            )
            self.assertTrue(retry.admitted, retry.reasons)
            self.assertEqual(retry.memory.event_id, result.memory.event_id)
            self.assertEqual(retry.adaptation.id, result.adaptation.id)
            self.assertEqual(retry.adaptation.status, "PROPOSED")
            self.assertEqual(len(runtime.memory.recent(20)), memory_count_before_retry)
            self.assertEqual(runtime.proposal_repository.get(result.adaptation.id)["id"], result.adaptation.id)

            # The bridge writes its execution event and learning writes a separate,
            # outcome-linked event; assert both exist without claiming cross-store atomicity.
            self.assertGreaterEqual(len(runtime.memory.recent(20)), 2)


    def _execute_composed_runtime(self, root, adapter, classifier):
        decision = DecisionItem(
            id="decision:negative-1",
            signal_kind="QUALITY_RISK",
            severity="HIGH",
            problem="Verify booking outcome",
            recommended_action="Execute a bounded verification command",
            owner="test-owner",
            status="APPROVED",
        )
        console = LiveOperatingConsole(
            date="2026-10-28",
            primary_objective="Trusted decision negative-path integration test",
        )
        command = console.add_command(
            "cmd:negative-1",
            objective="Verify a deterministic booking outcome",
            priority="P1",
            owner="test-owner",
            expected_output="A runtime execution with linked trusted receipt",
            source_decision_id=decision.id,
            next_action="Review the governed adaptation proposal",
        )
        runtime = build_trusted_learning_runtime(
            console=console,
            config=TrustedLearningRuntimeConfig(
                memory_path=str(root / "memory.json"),
                proposal_sqlite_path=str(root / "proposals.sqlite3"),
                replay_sqlite_path=str(root / "replay.sqlite3"),
                allowed_source_providers=("booking-provider",),
            ),
            trusted_source_adapter=adapter,
            classifier=classifier,
        )
        execution = runtime.bridge.execute(
            command.id,
            source_record_id="record:negative-1",
            verification_status="OUTCOME_LINKED",
            outcome_linked=True,
        )
        return decision, runtime, execution

    def _capture(self, runtime, decision, execution):
        return runtime.learning_service.capture_execution(
            decision,
            execution,
            evidence_id="evidence:e2e-1",
            policy_version="policy:e2e-v1",
            next_command="Review the proposed adaptation",
        )

    def test_receipt_mismatch_after_runtime_admission_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            adapter = DeterministicReceiptAdapter()
            classifier = FailedOutcomeClassifier()
            decision, runtime, execution = self._execute_composed_runtime(
                Path(tmp), adapter, classifier
            )
            # Simulate the provider returning changed content at the learning boundary.
            adapter.raw_observation = "booking outcome=changed-after-runtime"
            event_count_before = len(runtime.memory.recent(20))
            result = self._capture(runtime, decision, execution)
            self.assertFalse(result.admitted)
            self.assertIn("does not match runtime receipt", result.reasons[0])
            self.assertIsNone(result.memory)
            self.assertIsNone(result.adaptation)
            self.assertEqual(len(runtime.memory.recent(20)), event_count_before)
            self.assertEqual(classifier.fail, False)

    def test_unapproved_decision_fails_closed_without_learning_write(self):
        with tempfile.TemporaryDirectory() as tmp:
            decision, runtime, execution = self._execute_composed_runtime(
                Path(tmp), DeterministicReceiptAdapter(), FailedOutcomeClassifier()
            )
            decision = replace(decision, status="PENDING")
            event_count_before = len(runtime.memory.recent(20))
            result = self._capture(runtime, decision, execution)
            self.assertFalse(result.admitted)
            self.assertIn("not approved", result.reasons[0])
            self.assertIsNone(result.memory)
            self.assertIsNone(result.adaptation)
            self.assertEqual(len(runtime.memory.recent(20)), event_count_before)

    def test_replayed_receipt_is_rejected_by_composed_runtime(self):
        with tempfile.TemporaryDirectory() as tmp:
            adapter = DeterministicReceiptAdapter()
            decision, runtime, execution = self._execute_composed_runtime(
                Path(tmp), adapter, FailedOutcomeClassifier()
            )
            execution_id = execution.operating_loop.execution_id
            event_count_before = len(runtime.memory.recent(20))

            # The bridge already claimed this provider/record/content tuple.
            replay = runtime.bridge.trusted_source_verifier.verify(
                "record:negative-1",
                execution_id,
            )

            self.assertFalse(replay.verified)
            self.assertTrue(
                any("replay" in reason.lower() for reason in replay.reasons),
                replay.reasons,
            )
            self.assertEqual(len(runtime.memory.recent(20)), event_count_before)

    def test_cross_provider_receipt_substitution_fails_closed_at_learning_boundary(self):
        with tempfile.TemporaryDirectory() as tmp:
            adapter = DeterministicReceiptAdapter()
            decision, runtime, execution = self._execute_composed_runtime(
                Path(tmp), adapter, FailedOutcomeClassifier()
            )
            original_fetch = adapter.fetch_receipt

            def substituted_provider_receipt(source_record_id, execution_id):
                receipt = original_fetch(source_record_id, execution_id)
                return replace(receipt, provider_name="untrusted-provider")

            adapter.fetch_receipt = substituted_provider_receipt
            event_count_before = len(runtime.memory.recent(20))
            result = self._capture(runtime, decision, execution)
            self.assertFalse(result.admitted)
            self.assertIsNone(result.memory)
            self.assertIsNone(result.adaptation)
            self.assertEqual(len(runtime.memory.recent(20)), event_count_before)

    def test_stale_receipt_fails_closed_at_learning_boundary(self):
        with tempfile.TemporaryDirectory() as tmp:
            adapter = DeterministicReceiptAdapter()
            decision, runtime, execution = self._execute_composed_runtime(
                Path(tmp), adapter, FailedOutcomeClassifier()
            )
            original_fetch = adapter.fetch_receipt

            def stale_receipt(source_record_id, execution_id):
                receipt = original_fetch(source_record_id, execution_id)
                return replace(receipt, observed_at="2020-01-01T00:00:00+00:00")

            adapter.fetch_receipt = stale_receipt
            event_count_before = len(runtime.memory.recent(20))
            result = self._capture(runtime, decision, execution)
            self.assertFalse(result.admitted)
            self.assertIsNone(result.memory)
            self.assertIsNone(result.adaptation)
            self.assertEqual(len(runtime.memory.recent(20)), event_count_before)

    def test_receipt_source_record_substitution_fails_closed_at_learning_boundary(self):
        with tempfile.TemporaryDirectory() as tmp:
            adapter = DeterministicReceiptAdapter()
            decision, runtime, execution = self._execute_composed_runtime(
                Path(tmp), adapter, FailedOutcomeClassifier()
            )
            original_fetch = adapter.fetch_receipt

            def substituted_record_receipt(source_record_id, execution_id):
                receipt = original_fetch(source_record_id, execution_id)
                return replace(receipt, source_record_id="record:substituted")

            adapter.fetch_receipt = substituted_record_receipt
            event_count_before = len(runtime.memory.recent(20))
            result = self._capture(runtime, decision, execution)
            self.assertFalse(result.admitted)
            self.assertIsNone(result.memory)
            self.assertIsNone(result.adaptation)
            self.assertEqual(len(runtime.memory.recent(20)), event_count_before)

    def test_proposal_persistence_failure_leaves_memory_event_without_proposal(self):
        with tempfile.TemporaryDirectory() as tmp:
            decision, runtime, execution = self._execute_composed_runtime(
                Path(tmp), DeterministicReceiptAdapter(), FailedOutcomeClassifier()
            )
            event_count_before = len(runtime.memory.recent(20))

            def fail_proposal_write(*args, **kwargs):
                raise RuntimeError("simulated SQLite proposal-store outage")

            runtime.proposal_repository.get_or_create = fail_proposal_write
            with self.assertRaisesRegex(RuntimeError, "simulated SQLite proposal-store outage"):
                self._capture(runtime, decision, execution)

            # This intentionally records the current cross-store commit boundary:
            # JSON memory is durable before SQLite proposal persistence is attempted.
            self.assertEqual(len(runtime.memory.recent(20)), event_count_before + 1)
            self.assertEqual(
                len([
                    item for item in runtime.memory.recent(20)
                    if item.event_id.startswith("learning:")
                ]),
                1,
            )
            self.assertEqual(
                runtime.proposal_repository.health_check(),
                True,
            )

    def test_classifier_failure_fails_closed_without_learning_write(self):
        with tempfile.TemporaryDirectory() as tmp:
            classifier = FailedOutcomeClassifier()
            classifier.fail = True
            decision, runtime, execution = self._execute_composed_runtime(
                Path(tmp), DeterministicReceiptAdapter(), classifier
            )
            event_count_before = len(runtime.memory.recent(20))
            result = self._capture(runtime, decision, execution)
            self.assertFalse(result.admitted)
            self.assertIn("classification failed closed", result.reasons[0])
            self.assertIsNone(result.memory)
            self.assertIsNone(result.adaptation)
            # Bridge execution event exists, but no outcome-linked learning event was added.
            self.assertEqual(len(runtime.memory.recent(20)), event_count_before)


if __name__ == "__main__":
    unittest.main()
