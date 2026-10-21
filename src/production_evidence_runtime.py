"""Explicit production configuration for evidence-admitting OIA runtimes.

This factory wires local durable replay protection and refuses configuration
that could silently fall back to the process-local in-memory replay store.
It does not configure or authenticate any external provider.
"""
from __future__ import annotations

from dataclasses import dataclass

from src.live_operating_console import LiveOperatingConsole
from src.live_runtime_bridge import LiveRuntimeBridge
from src.receipt_replay_store import SQLiteReceiptReplayStore
from src.trusted_source_receipt import TrustedSourceAdapter


@dataclass(frozen=True)
class ProductionEvidenceRuntimeConfig:
    """Required deployment inputs for a local/single-host evidence runtime."""

    sqlite_path: str
    allowed_source_providers: tuple[str, ...]

    def validate(self) -> None:
        if not isinstance(self.sqlite_path, str) or not self.sqlite_path.strip():
            raise ValueError("sqlite_path must be a non-empty persistent file path")
        sqlite_path = self.sqlite_path.strip()
        if sqlite_path == ":memory:" or sqlite_path.lower().startswith("file:"):
            # URI paths can enable shared in-memory databases or other SQLite URI
            # modes; this production factory deliberately accepts file paths only.
            raise ValueError("production evidence runtime requires a file-backed SQLite path, not an in-memory/URI database")
        if not isinstance(self.allowed_source_providers, tuple):
            raise ValueError("allowed_source_providers must be an explicit tuple")
        if any(
            not isinstance(provider, str) or not provider.strip()
            for provider in self.allowed_source_providers
        ):
            raise ValueError("provider names must be non-empty strings")
        providers = tuple(provider.strip() for provider in self.allowed_source_providers)
        if not providers:
            raise ValueError("at least one explicit allowed source provider is required")
        if len(set(providers)) != len(providers):
            raise ValueError("allowed source providers must be unique")


def build_production_evidence_runtime(
    console: LiveOperatingConsole,
    *,
    config: ProductionEvidenceRuntimeConfig,
    trusted_source_adapter: TrustedSourceAdapter,
) -> LiveRuntimeBridge:
    """Construct a fail-closed evidence runtime for local/single-host use.

    A provider adapter must still implement real provider-specific authenticity
    and execution-attribution checks. Tests with fake adapters do not prove that.
    """
    if not isinstance(console, LiveOperatingConsole):
        raise TypeError("console must be a LiveOperatingConsole")
    if not isinstance(config, ProductionEvidenceRuntimeConfig):
        raise TypeError("config must be a ProductionEvidenceRuntimeConfig")
    if trusted_source_adapter is None:
        raise ValueError("trusted_source_adapter is required for evidence runtime")
    config.validate()

    try:
        adapter_provider = getattr(trusted_source_adapter, "provider_name", "")
    except Exception:
        raise ValueError(
            "trusted source adapter provider_name could not be read safely"
        ) from None
    if not isinstance(adapter_provider, str) or not adapter_provider.strip():
        raise ValueError("trusted source adapter must declare a provider_name")
    if adapter_provider.strip() not in {
        provider.strip() for provider in config.allowed_source_providers
    }:
        raise ValueError("trusted source adapter provider is not explicitly allowlisted")

    store = SQLiteReceiptReplayStore(config.sqlite_path.strip())
    if not store.health_check():
        raise RuntimeError("SQLite receipt replay store health check failed")

    return LiveRuntimeBridge(
        console=console,
        trusted_source_adapter=trusted_source_adapter,
        allowed_source_providers=tuple(
            provider.strip() for provider in config.allowed_source_providers
        ),
        receipt_replay_store=store,
        require_durable_replay_store=True,
    )
