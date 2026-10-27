"""Explicit, fail-closed composition for the trusted learning service.

This factory wires durable local stores but does not create or authenticate a
provider adapter/classifier. Callers must supply real, provider-specific
implementations. The memory JSON file and proposal SQLite file are separate
persistence boundaries; this factory does not make them transactionally atomic.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from src.adaptation_proposal_repository import SQLiteAdaptationProposalRepository
from src.operating_memory import OperatingMemory
from src.trusted_decision_learning_service import (
    TrustedDecisionLearningService,
    TrustedOutcomeClassifier,
)
from src.trusted_source_receipt import TrustedSourceReceiptVerifier


@dataclass(frozen=True)
class TrustedLearningServiceConfig:
    """Required file-backed paths for a single-host learning configuration."""

    memory_path: str
    proposal_sqlite_path: str

    def resolved_paths(self) -> tuple[Path, Path]:
        paths = []
        for name, value in (
            ("memory_path", self.memory_path),
            ("proposal_sqlite_path", self.proposal_sqlite_path),
        ):
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be a non-empty file path")
            normalized = value.strip()
            if normalized == ":memory:" or normalized.lower().startswith("file:"):
                raise ValueError(f"{name} must be a regular persistent file path")
            paths.append(Path(normalized).expanduser().resolve())
        if paths[0] == paths[1]:
            raise ValueError("memory_path and proposal_sqlite_path must be different files")
        return paths[0], paths[1]

    def validate(self) -> None:
        self.resolved_paths()


def build_trusted_learning_service(
    *,
    config: TrustedLearningServiceConfig,
    receipt_verifier: TrustedSourceReceiptVerifier,
    classifier: TrustedOutcomeClassifier,
) -> TrustedDecisionLearningService:
    """Build the service only when real trust components and durable paths exist.

    This is a composition helper, not an application entrypoint or deployment
    proof. Provider authenticity and classifier correctness remain the
    responsibility of the supplied provider-specific implementations.
    """
    if not isinstance(config, TrustedLearningServiceConfig):
        raise TypeError("config must be a TrustedLearningServiceConfig")
    memory_path, proposal_path = config.resolved_paths()
    if receipt_verifier is None or not callable(
        getattr(receipt_verifier, "verify", None)
    ):
        raise ValueError("a receipt verifier with a callable verify method is required")
    if classifier is None or not callable(getattr(classifier, "classify", None)):
        raise ValueError("a provider-specific classifier with a callable classify method is required")

    memory_path.parent.mkdir(parents=True, exist_ok=True)
    proposal_path.parent.mkdir(parents=True, exist_ok=True)
    memory = OperatingMemory(path=memory_path)
    repository = SQLiteAdaptationProposalRepository(str(proposal_path))
    return TrustedDecisionLearningService(
        classifier=classifier,
        receipt_verifier=receipt_verifier,
        memory=memory,
        adaptation_proposal_repository=repository,
    )
