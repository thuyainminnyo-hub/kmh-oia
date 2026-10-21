"""Production bootstrap joining signed artifact loading, learning service, and orchestrator.

The policy binder is mandatory because this repository does not prescribe the concrete
policy artifact format or runtime policy-engine interface. Production must supply that
adapter explicitly; a missing or failing binder prevents the assembly from being returned.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Mapping, Any

from src.governed_decision_orchestrator import GovernedDecisionOrchestrator
from src.learning_admission_repository import SQLiteLearningAdmissionRepository
from src.live_operating_console import LiveOperatingConsole
from src.live_runtime_bridge import LiveRuntimeBridge
from src.operating_memory import OperatingMemory
from src.production_artifact_trust import (
    ProductionArtifactTrustConfigError,
    load_production_runtime_artifacts,
)
from src.runtime_artifact_attestation import RuntimeArtifactAttestation
from src.runtime_artifact_loader import VerifiedRuntimeArtifacts
from src.trusted_decision_learning_service import TrustedDecisionLearningService
from src.trusted_source_receipt import TrustedSourceReceiptVerifier
from src.decision_queue import DecisionQueue


class ProductionRuntimeAssemblyError(RuntimeError):
    """Raised when a safe production runtime assembly cannot be completed."""


@dataclass(frozen=True)
class ProductionRuntimeAssembly:
    orchestrator: GovernedDecisionOrchestrator
    learning_service: TrustedDecisionLearningService
    artifacts: VerifiedRuntimeArtifacts


def build_production_runtime_assembly(
    *,
    queue: DecisionQueue,
    console: LiveOperatingConsole,
    runtime_bridge: LiveRuntimeBridge,
    receipt_verifier: TrustedSourceReceiptVerifier | None,
    memory: OperatingMemory,
    repository: SQLiteLearningAdmissionRepository,
    classifier_path: str | Path,
    policy_path: str | Path,
    attestation: RuntimeArtifactAttestation,
    classifier_loader: Callable[[bytes], Any],
    policy_loader: Callable[[bytes], Any],
    policy_runtime_binder: Callable[[GovernedDecisionOrchestrator, Any], None],
    environ: Mapping[str, str] | None = None,
) -> ProductionRuntimeAssembly:
    """Verify artifacts, create learning service, then require an explicit policy binder."""
    if not callable(policy_runtime_binder):
        raise ProductionRuntimeAssemblyError(
            "a concrete policy_runtime_binder is required for production assembly"
        )
    try:
        artifacts = load_production_runtime_artifacts(
            classifier_path, policy_path,
            attestation=attestation,
            classifier_loader=classifier_loader,
            policy_loader=policy_loader,
            environ=environ,
        )
        service = TrustedDecisionLearningService(
            classifier=artifacts.classifier,
            receipt_verifier=receipt_verifier,
            memory=memory,
            repository=repository,
            runtime_artifacts=artifacts,
        )
        orchestrator = GovernedDecisionOrchestrator(
            queue, console, runtime_bridge=runtime_bridge, learning_service=service,
        )
        policy_runtime_binder(orchestrator, artifacts.policy)
        return ProductionRuntimeAssembly(
            orchestrator=orchestrator, learning_service=service, artifacts=artifacts,
        )
    except ProductionArtifactTrustConfigError as exc:
        raise ProductionRuntimeAssemblyError(
            "production artifact trust or loading failed closed"
        ) from exc
    except ProductionRuntimeAssemblyError:
        raise
    except Exception as exc:
        raise ProductionRuntimeAssemblyError(
            "production runtime assembly or policy binding failed closed"
        ) from exc
