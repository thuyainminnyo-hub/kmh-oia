import base64
import hashlib
import json
import tempfile
import unittest
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from src.decision_queue import DecisionQueue
from src.learning_admission_repository import SQLiteLearningAdmissionRepository
from src.live_operating_console import LiveOperatingConsole
from src.live_runtime_bridge import LiveRuntimeBridge
from src.operating_memory import OperatingMemory
from src.production_runtime_assembly import (
    ProductionRuntimeAssemblyError, build_production_runtime_assembly,
)
from src.runtime_artifact_attestation import RuntimeArtifactAttestation, canonical_attestation_payload


class LoadedTestClassifier:
    def __init__(self, payload: bytes):
        self.payload = payload

    def classify(self, decision, execution, receipt):
        raise AssertionError("test factory does not execute the classifier")


class ProductionRuntimeAssemblyTests(unittest.TestCase):
    def setUp(self):
        self.classifier_bytes = b"phase807-classifier-model"
        self.policy_bytes = b"phase807-policy-rules"
        self.source_revision = "f" * 40
        self.private_key = Ed25519PrivateKey.generate()
        public_key = self.private_key.public_key().public_bytes(
            encoding=serialization.Encoding.Raw, format=serialization.PublicFormat.Raw,
        )
        self.environ = {
            "KMH_OIA_ENVIRONMENT": "production",
            "KMH_OIA_ATTESTATION_TRUSTED_PUBLIC_KEYS_JSON": json.dumps({
                "prod-release-key-807": base64.b64encode(public_key).decode("ascii")
            }),
            "KMH_OIA_ATTESTATION_ALLOWED_ISSUERS": "kmh-release-signer",
            "KMH_OIA_ATTESTATION_ALLOWED_SUBJECTS": "repo:thuyainminnyo-hub/kmh-oia:ref:refs/heads/main",
            "KMH_OIA_ATTESTATION_EXPECTED_SOURCE_REVISION": self.source_revision,
            "KMH_OIA_ATTESTATION_MAX_AGE_SECONDS": "1800",
            "KMH_OIA_ATTESTATION_MAX_CLOCK_SKEW_SECONDS": "60",
        }
        now = datetime.now(timezone.utc)
        statement = RuntimeArtifactAttestation(
            classifier_sha256=hashlib.sha256(self.classifier_bytes).hexdigest(),
            policy_sha256=hashlib.sha256(self.policy_bytes).hexdigest(),
            issuer="kmh-release-signer",
            subject="repo:thuyainminnyo-hub/kmh-oia:ref:refs/heads/main",
            attestation_id="phase807-assembly-test",
            key_id="prod-release-key-807",
            source_revision=self.source_revision,
            build_run_id="build-run-807",
            issued_at=now.isoformat().replace("+00:00", "Z"),
        )
        self.attestation = replace(statement, signature=base64.b64encode(
            self.private_key.sign(canonical_attestation_payload(statement))
        ).decode("ascii"))
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.classifier_path = Path(self.tmp.name) / "classifier.bin"
        self.policy_path = Path(self.tmp.name) / "policy.bin"
        self.classifier_path.write_bytes(self.classifier_bytes)
        self.policy_path.write_bytes(self.policy_bytes)

    def make_inputs(self):
        console = LiveOperatingConsole(date="2026-10-21", primary_objective="Governed production runtime")
        queue = DecisionQueue()
        runtime = LiveRuntimeBridge(console)
        repository = SQLiteLearningAdmissionRepository(Path(self.tmp.name) / "learning.sqlite3")
        return queue, console, runtime, OperatingMemory(), repository

    def test_factory_binds_signed_artifacts_service_and_orchestrator(self):
        queue, console, runtime, memory, repository = self.make_inputs()
        binder_calls = []
        assembly = build_production_runtime_assembly(
            queue=queue, console=console, runtime_bridge=runtime,
            receipt_verifier=None, memory=memory, repository=repository,
            classifier_path=self.classifier_path, policy_path=self.policy_path,
            attestation=self.attestation, environ=self.environ,
            classifier_loader=lambda payload: LoadedTestClassifier(payload),
            policy_loader=lambda payload: {"policy_payload": payload},
            policy_runtime_binder=lambda orchestrator, policy: binder_calls.append((orchestrator, policy)),
        )
        self.assertIs(assembly.orchestrator.learning_service, assembly.learning_service)
        self.assertIs(assembly.learning_service._runtime_artifacts, assembly.artifacts)
        self.assertIs(assembly.learning_service._classifier, assembly.artifacts.classifier)
        self.assertEqual(assembly.artifacts.classifier.payload, self.classifier_bytes)
        self.assertEqual(assembly.artifacts.policy["policy_payload"], self.policy_bytes)
        self.assertEqual(len(binder_calls), 1)
        self.assertIs(binder_calls[0][0], assembly.orchestrator)
        self.assertIs(binder_calls[0][1], assembly.artifacts.policy)

    def test_missing_policy_binder_blocks_assembly_before_any_loader_runs(self):
        queue, console, runtime, memory, repository = self.make_inputs()
        calls = []
        with self.assertRaisesRegex(ProductionRuntimeAssemblyError, "policy_runtime_binder is required"):
            build_production_runtime_assembly(
                queue=queue, console=console, runtime_bridge=runtime,
                receipt_verifier=None, memory=memory, repository=repository,
                classifier_path=self.classifier_path, policy_path=self.policy_path,
                attestation=self.attestation, environ=self.environ,
                classifier_loader=lambda payload: calls.append("classifier"),
                policy_loader=lambda payload: calls.append("policy"),
                policy_runtime_binder=None,
            )
        self.assertEqual(calls, [])

    def test_policy_binder_failure_does_not_return_an_assembly(self):
        queue, console, runtime, memory, repository = self.make_inputs()
        with self.assertRaisesRegex(ProductionRuntimeAssemblyError, "policy binding failed closed"):
            build_production_runtime_assembly(
                queue=queue, console=console, runtime_bridge=runtime,
                receipt_verifier=None, memory=memory, repository=repository,
                classifier_path=self.classifier_path, policy_path=self.policy_path,
                attestation=self.attestation, environ=self.environ,
                classifier_loader=lambda payload: LoadedTestClassifier(payload),
                policy_loader=lambda payload: {"policy_payload": payload},
                policy_runtime_binder=lambda orchestrator, policy: (_ for _ in ()).throw(RuntimeError("private details")),
            )


if __name__ == "__main__":
    unittest.main()
