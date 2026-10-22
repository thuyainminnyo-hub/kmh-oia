"""Build the production evidence runtime only after bundle release verification succeeds."""
from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from typing import Mapping

from src.live_operating_console import LiveOperatingConsole
from src.live_runtime_bridge import LiveRuntimeBridge
from src.production_evidence_runtime import (
    ProductionEvidenceRuntimeConfig,
    build_production_evidence_runtime,
)
from src.trusted_source_receipt import TrustedSourceAdapter
from scripts.verify_runtime_bundle_release import verify_runtime_bundle_release


def build_verified_production_evidence_runtime(
    console: LiveOperatingConsole,
    *,
    config: ProductionEvidenceRuntimeConfig,
    trusted_source_adapter: TrustedSourceAdapter,
    bundle_path: str | Path,
    attestation_path: str | Path,
    expected_source_revision: str,
    expected_build_run_id: str,
    expected_artifact_id: str,
    expected_artifact_name: str,
    expected_artifact_digest: str,
    trusted_public_keys: Mapping[str, bytes],
    allowed_issuers: tuple[str, ...],
    allowed_subjects: tuple[str, ...],
    max_age_seconds: int = 3600,
    max_clock_skew_seconds: int = 60,
) -> LiveRuntimeBridge:
    """Verify the exact source bundle and attestation before constructing the runtime.

    Producer run/artifact metadata must be fetched from a trusted provider API by the
    deployment/bootstrap caller. This function authenticates the local bundle against
    those observed fields and only then constructs the evidence runtime. It does not
    itself fetch remote metadata or prove deployment.
    """
    if not isinstance(config, ProductionEvidenceRuntimeConfig):
        raise TypeError("config must be a ProductionEvidenceRuntimeConfig")

    # Validate external arguments first, then bind exactly those verified values into
    # the production factory config so its own startup gate cannot be bypassed.
    verify_runtime_bundle_release(
        bundle_path,
        attestation_path,
        expected_source_revision=expected_source_revision,
        expected_build_run_id=expected_build_run_id,
        expected_artifact_id=expected_artifact_id,
        expected_artifact_name=expected_artifact_name,
        expected_artifact_digest=expected_artifact_digest,
        trusted_public_keys=trusted_public_keys,
        allowed_issuers=allowed_issuers,
        allowed_subjects=allowed_subjects,
        max_age_seconds=max_age_seconds,
        max_clock_skew_seconds=max_clock_skew_seconds,
    )
    verified_config = replace(
        config,
        runtime_bundle_path=str(bundle_path),
        runtime_attestation_path=str(attestation_path),
        expected_source_revision=expected_source_revision,
        expected_build_run_id=expected_build_run_id,
        expected_artifact_id=expected_artifact_id,
        expected_artifact_name=expected_artifact_name,
        expected_artifact_digest=expected_artifact_digest,
        trusted_release_public_keys=trusted_public_keys,
        allowed_release_issuers=allowed_issuers,
        allowed_release_subjects=allowed_subjects,
        release_attestation_max_age_seconds=max_age_seconds,
        require_signed_release_bundle=True,
    )
    return build_production_evidence_runtime(
        console,
        config=verified_config,
        trusted_source_adapter=trusted_source_adapter,
    )
