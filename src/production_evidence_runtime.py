"""Explicit production configuration for evidence-admitting OIA runtimes.

This factory wires local durable replay protection and refuses configuration
that could silently fall back to the process-local in-memory replay store.
It does not configure or authenticate any external provider.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

from scripts.verify_runtime_bundle_release import (
    RuntimeBundleReleaseRejected,
    verify_runtime_bundle_release,
)


from src.live_operating_console import LiveOperatingConsole
from src.live_runtime_bridge import LiveRuntimeBridge
from src.receipt_replay_store import SQLiteReceiptReplayStore
from src.trusted_source_receipt import TrustedSourceAdapter


@dataclass(frozen=True)
class ProductionEvidenceRuntimeConfig:
    """Required deployment inputs for a local/single-host evidence runtime."""

    sqlite_path: str
    allowed_source_providers: tuple[str, ...]
    runtime_bundle_path: str = ""
    runtime_attestation_path: str = ""
    runtime_source_revision: str = ""
    runtime_build_run_id: str = ""
    runtime_artifact_id: str = ""
    runtime_artifact_name: str = ""
    runtime_artifact_digest: str = ""
    runtime_trusted_public_keys: Mapping[str, bytes] | None = None
    runtime_allowed_issuers: tuple[str, ...] = ()
    runtime_allowed_subjects: tuple[str, ...] = ()

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
        release_fields = (
            self.runtime_bundle_path, self.runtime_attestation_path, self.runtime_source_revision,
            self.runtime_build_run_id, self.runtime_artifact_id, self.runtime_artifact_name,
            self.runtime_artifact_digest,
        )
        if any(not isinstance(value, str) or not value.strip() for value in release_fields):
            raise ValueError("runtime bundle paths and expected provenance fields are required")
        if not self.runtime_trusted_public_keys:
            raise ValueError("runtime bundle trusted public keys are required")
        if not isinstance(self.runtime_allowed_issuers, tuple) or not self.runtime_allowed_issuers:
            raise ValueError("runtime bundle issuer allowlist must be an explicit non-empty tuple")
        if not isinstance(self.runtime_allowed_subjects, tuple) or not self.runtime_allowed_subjects:
            raise ValueError("runtime bundle subject allowlist must be an explicit non-empty tuple")
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

    # Authenticate the exact runtime bundle before creating any live bridge.
    # This proves release bytes/provenance only, not deployment or provider authenticity.
    verify_runtime_bundle_release(
        config.runtime_bundle_path,
        config.runtime_attestation_path,
        expected_source_revision=config.runtime_source_revision,
        expected_build_run_id=config.runtime_build_run_id,
        expected_artifact_id=config.runtime_artifact_id,
        expected_artifact_name=config.runtime_artifact_name,
        expected_artifact_digest=config.runtime_artifact_digest,
        trusted_public_keys=config.runtime_trusted_public_keys or {},
        allowed_issuers=config.runtime_allowed_issuers,
        allowed_subjects=config.runtime_allowed_subjects,
    )

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
