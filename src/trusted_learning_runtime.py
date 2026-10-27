"""Explicit composition of the durable evidence bridge and trusted learning service.

This is an opt-in single-host composition helper, not a default application
entrypoint or proof of provider authenticity/deployment readiness.
Memory JSON and the two SQLite stores are separate persistence boundaries;
there is no transaction spanning all three.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from src.adaptation_proposal_repository import SQLiteAdaptationProposalRepository
from src.live_operating_console import LiveOperatingConsole
from src.live_runtime_bridge import LiveRuntimeBridge
from src.operating_memory import OperatingMemory
from src.receipt_replay_store import SQLiteReceiptReplayStore
from src.trusted_decision_learning_service import (
    TrustedDecisionLearningService,
    TrustedOutcomeClassifier,
)
from src.trusted_source_receipt import TrustedSourceAdapter


@dataclass(frozen=True)
class TrustedLearningRuntimeConfig:
    """Persistent local paths and explicit provider allowlist for one host."""

    memory_path: str
    proposal_sqlite_path: str
    replay_sqlite_path: str
    allowed_source_providers: tuple[str, ...]

    def resolved_paths(self) -> tuple[Path, Path, Path]:
        paths: list[Path] = []
        for name, value in (
            ("memory_path", self.memory_path),
            ("proposal_sqlite_path", self.proposal_sqlite_path),
            ("replay_sqlite_path", self.replay_sqlite_path),
        ):
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be a non-empty persistent file path")
            normalized = value.strip()
            if normalized == ":memory:" or normalized.lower().startswith("file:"):
                raise ValueError(f"{name} must be a regular persistent file path")
            paths.append(Path(normalized).expanduser().resolve())
        if len(set(paths)) != len(paths):
            raise ValueError("memory, proposal, and replay paths must be distinct files")
        return paths[0], paths[1], paths[2]

    def validate(self) -> None:
        self.resolved_paths()
        providers = self.allowed_source_providers
        if not isinstance(providers, tuple) or not providers:
            raise ValueError("an explicit non-empty provider allowlist tuple is required")
        if any(not isinstance(p, str) or not p.strip() for p in providers):
            raise ValueError("provider names must be non-empty strings")
        normalized = tuple(p.strip() for p in providers)
        if len(set(normalized)) != len(normalized):
            raise ValueError("provider allowlist entries must be unique")


@dataclass(frozen=True)
class TrustedLearningRuntime:
    """The bridge and learning service sharing memory and receipt verification."""

    bridge: LiveRuntimeBridge
    learning_service: TrustedDecisionLearningService
    memory: OperatingMemory
    replay_store: SQLiteReceiptReplayStore
    proposal_repository: SQLiteAdaptationProposalRepository


def build_trusted_learning_runtime(
    *,
    console: LiveOperatingConsole,
    config: TrustedLearningRuntimeConfig,
    trusted_source_adapter: TrustedSourceAdapter,
    classifier: TrustedOutcomeClassifier,
) -> TrustedLearningRuntime:
    """Compose durable local evidence admission and trusted learning explicitly.

    Callers must provide genuine provider-specific authentication and a correct
    classifier. Fake adapters can test wiring only; they do not prove authenticity.
    """
    if not isinstance(console, LiveOperatingConsole):
        raise TypeError("console must be a LiveOperatingConsole")
    if not isinstance(config, TrustedLearningRuntimeConfig):
        raise TypeError("config must be a TrustedLearningRuntimeConfig")
    config.validate()
    if trusted_source_adapter is None:
        raise ValueError("trusted_source_adapter is required")
    if classifier is None or not callable(getattr(classifier, "classify", None)):
        raise ValueError("a provider-specific classifier with callable classify is required")
    try:
        provider = trusted_source_adapter.provider_name
    except Exception:
        raise ValueError("adapter provider_name could not be read safely") from None
    if not isinstance(provider, str) or not provider.strip():
        raise ValueError("trusted source adapter must declare provider_name")
    if provider.strip() not in {p.strip() for p in config.allowed_source_providers}:
        raise ValueError("trusted source adapter provider is not explicitly allowlisted")

    memory_path, proposal_path, replay_path = config.resolved_paths()
    for path in (memory_path, proposal_path, replay_path):
        path.parent.mkdir(parents=True, exist_ok=True)

    memory = OperatingMemory(path=memory_path)
    replay_store = SQLiteReceiptReplayStore(str(replay_path))
    if not replay_store.health_check():
        raise RuntimeError("SQLite receipt replay store health check failed")
    bridge = LiveRuntimeBridge(
        console=console,
        memory=memory,
        trusted_source_adapter=trusted_source_adapter,
        allowed_source_providers=tuple(p.strip() for p in config.allowed_source_providers),
        receipt_replay_store=replay_store,
        require_durable_replay_store=True,
    )
    repository = SQLiteAdaptationProposalRepository(str(proposal_path))
    learning_service = TrustedDecisionLearningService(
        classifier=classifier,
        receipt_verifier=bridge.trusted_source_verifier,
        memory=memory,
        adaptation_proposal_repository=repository,
    )
    return TrustedLearningRuntime(
        bridge=bridge,
        learning_service=learning_service,
        memory=memory,
        replay_store=replay_store,
        proposal_repository=repository,
    )
