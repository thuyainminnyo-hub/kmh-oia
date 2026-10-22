"""Explicit production configuration for evidence-admitting OIA runtimes.

This factory wires local durable replay protection. When a signed release bundle
is configured, it verifies the bundle and attestation before constructing the
execution bridge. It does not configure or authenticate any external provider.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

from src.live_operating_console import LiveOperatingConsole
from src.live_runtime_bridge import LiveRuntimeBridge
from src.receipt_replay_store import SQLiteReceiptReplayStore
from src.trusted_source_receipt import TrustedSourceAdapter
from scripts.verify_runtime_bundle_release import verify_runtime_bundle_release


@dataclass(frozen=True)
class ProductionEvidenceRuntimeConfig:
    """Required deployment inputs for local/single-host evidence runtime.

    Supplying any release-attestation field activates strict bundle verification;
    all release fields and a public-key trust root must then be present together.
    """
    sqlite_path: str
    allowed_source_providers: tuple[str, ...]
    runtime_bundle_path: str | None = None
    runtime_source_root: str | None = None
    runtime_attestation_path: str | None = None
    expected_source_revision: str | None = None
    expected_build_run_id: str | None = None
    expected_artifact_id: str | None = None
    expected_artifact_name: str | None = None
    expected_artifact_digest: str | None = None
    trusted_release_public_keys: Mapping[str, bytes] | None = None
    allowed_release_issuers: tuple[str, ...] = ()
    allowed_release_subjects: tuple[str, ...] = ()
    release_attestation_max_age_seconds: int = 3600
    # Secure default: production startup requires verified signed release provenance.
    # Only isolated local/unit-test setups should explicitly disable this gate.
    require_signed_release_bundle: bool = True

    def validate(self) -> None:
        if not isinstance(self.sqlite_path, str) or not self.sqlite_path.strip():
            raise ValueError("sqlite_path must be a non-empty persistent file path")
        sqlite_path = self.sqlite_path.strip()
        if sqlite_path == ":memory:" or sqlite_path.lower().startswith("file:"):
            raise ValueError("production evidence runtime requires a file-backed SQLite path, not an in-memory/URI database")
        if not isinstance(self.allowed_source_providers, tuple):
            raise ValueError("allowed_source_providers must be an explicit tuple")
        if any(not isinstance(provider, str) or not provider.strip() for provider in self.allowed_source_providers):
            raise ValueError("provider names must be non-empty strings")
        providers = tuple(provider.strip() for provider in self.allowed_source_providers)
        if not providers:
            raise ValueError("at least one explicit allowed source provider is required")
        if len(set(providers)) != len(providers):
            raise ValueError("allowed source providers must be unique")

        if not isinstance(self.require_signed_release_bundle, bool):
            raise ValueError("require_signed_release_bundle must be an explicit boolean")

        release_fields = (
            self.runtime_bundle_path, self.runtime_source_root, self.runtime_attestation_path, self.expected_source_revision,
            self.expected_build_run_id, self.expected_artifact_id, self.expected_artifact_name,
            self.expected_artifact_digest,
        )
        any_release_configured = any(value is not None for value in release_fields) or self.trusted_release_public_keys is not None or bool(self.allowed_release_issuers) or bool(self.allowed_release_subjects)
        if self.require_signed_release_bundle and not any_release_configured:
            raise ValueError("production startup requires a signed runtime release bundle and attestation")
        if any_release_configured:
            if any(not isinstance(value, str) or not value.strip() for value in release_fields):
                raise ValueError("release bundle activation requires every bundle, attestation, source SHA and producer/artifact metadata field")
            if not self.trusted_release_public_keys:
                raise ValueError("release bundle activation requires an explicit trusted public-key map")
            if not self.allowed_release_issuers or any(not isinstance(value, str) or not value.strip() for value in self.allowed_release_issuers):
                raise ValueError("release bundle activation requires an explicit issuer allowlist")
            if not self.allowed_release_subjects or any(not isinstance(value, str) or not value.strip() for value in self.allowed_release_subjects):
                raise ValueError("release bundle activation requires an explicit subject allowlist")
            if isinstance(self.release_attestation_max_age_seconds, bool) or not isinstance(self.release_attestation_max_age_seconds, int) or self.release_attestation_max_age_seconds <= 0:
                raise ValueError("release_attestation_max_age_seconds must be a positive integer")
            if self.expected_artifact_name != "kmh-oia-runtime-bundle":
                raise ValueError("release artifact name does not match the approved runtime bundle name")

    def validate_release_bundle(self) -> dict[str, str | int] | None:
        self.validate()
        if self.runtime_bundle_path is None:
            return None
        try:
            return verify_runtime_bundle_release(
                self.runtime_bundle_path,
                self.runtime_attestation_path or "",
                expected_source_revision=self.expected_source_revision or "",
                expected_build_run_id=self.expected_build_run_id or "",
                expected_artifact_id=self.expected_artifact_id or "",
                expected_artifact_name=self.expected_artifact_name or "",
                expected_artifact_digest=self.expected_artifact_digest or "",
                runtime_source_root=self.runtime_source_root or "",
                trusted_public_keys=self.trusted_release_public_keys or {},
                allowed_issuers=self.allowed_release_issuers,
                allowed_subjects=self.allowed_release_subjects,
                max_age_seconds=self.release_attestation_max_age_seconds,
            )
        except Exception as exc:
            # Keep upstream bundle paths, payloads, and cryptographic details out of
            # the public startup error. The underlying verification remains fail-closed.
            raise ValueError("configured runtime release bundle or provenance did not verify") from exc


def build_production_evidence_runtime(
    console: LiveOperatingConsole,
    *,
    config: ProductionEvidenceRuntimeConfig,
    trusted_source_adapter: TrustedSourceAdapter,
) -> LiveRuntimeBridge:
    """Construct a fail-closed evidence runtime for local/single-host use.

    The configured on-disk runtime source tree must match the signed release bundle,
    and the attestation must verify before the bridge or replay store is created.
    A provider adapter must separately perform
    real provider authenticity and execution-attribution checks.
    """
    if not isinstance(console, LiveOperatingConsole):
        raise TypeError("console must be a LiveOperatingConsole")
    if not isinstance(config, ProductionEvidenceRuntimeConfig):
        raise TypeError("config must be a ProductionEvidenceRuntimeConfig")
    if trusted_source_adapter is None:
        raise ValueError("trusted_source_adapter is required for evidence runtime")
    config.validate()
    config.validate_release_bundle()

    try:
        adapter_provider = getattr(trusted_source_adapter, "provider_name", "")
    except Exception:
        raise ValueError("trusted source adapter provider_name could not be read safely") from None
    if not isinstance(adapter_provider, str) or not adapter_provider.strip():
        raise ValueError("trusted source adapter must declare a provider_name")
    if adapter_provider.strip() not in {provider.strip() for provider in config.allowed_source_providers}:
        raise ValueError("trusted source adapter provider is not explicitly allowlisted")

    store = SQLiteReceiptReplayStore(config.sqlite_path.strip())
    if not store.health_check():
        raise RuntimeError("SQLite receipt replay store health check failed")

    return LiveRuntimeBridge(
        console=console,
        trusted_source_adapter=trusted_source_adapter,
        allowed_source_providers=tuple(provider.strip() for provider in config.allowed_source_providers),
        receipt_replay_store=store,
        require_durable_replay_store=True,
    )
