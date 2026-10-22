"""Fail-closed consumer gate for accepting an attested KMH OIA runtime source bundle."""
from __future__ import annotations
import hashlib
from pathlib import Path
from typing import Mapping
from src.runtime_bundle_attestation import Ed25519RuntimeBundleAttestationVerifier
from src.runtime_bundle_attestation_io import load_runtime_bundle_attestation
from scripts.validate_runtime_bundle import validate_runtime_bundle

class RuntimeBundleReleaseRejected(ValueError):
    """Raised when source-bundle bytes or provenance cannot be authenticated."""

def verify_runtime_bundle_release(
    bundle_path: str | Path, attestation_path: str | Path, *,
    expected_source_revision: str, expected_build_run_id: str, expected_artifact_id: str,
    expected_artifact_name: str, expected_artifact_digest: str,
    trusted_public_keys: Mapping[str, bytes], allowed_issuers: tuple[str, ...],
    allowed_subjects: tuple[str, ...], max_age_seconds: int = 3600,
    max_clock_skew_seconds: int = 60,
) -> dict[str, str | int]:
    """Verify the bytes and signature against producer metadata fetched from a trusted source.

    This function does not fetch GitHub metadata or prove deployment; the caller supplies
    expected fields obtained independently from the trusted producer-run/artifact API.
    """
    try:
        if not isinstance(expected_source_revision, str):
            raise RuntimeBundleReleaseRejected("expected source revision must be a full lowercase Git SHA")
        expected_sha = expected_source_revision.strip().lower()
        if len(expected_sha) != 40 or any(c not in "0123456789abcdef" for c in expected_sha):
            raise RuntimeBundleReleaseRejected("expected source revision must be a full lowercase 40-character SHA")
        for name, value in (("expected_build_run_id", expected_build_run_id),
                            ("expected_artifact_id", expected_artifact_id)):
            if not isinstance(value, str) or not value.isdigit() or value.startswith("0"):
                raise RuntimeBundleReleaseRejected(f"{name} must be a canonical positive decimal ID")
        if expected_artifact_name != "kmh-oia-runtime-bundle":
            raise RuntimeBundleReleaseRejected("artifact name is not the approved runtime bundle name")
        if (not isinstance(expected_artifact_digest, str) or len(expected_artifact_digest) != 71
                or not expected_artifact_digest.startswith("sha256:")
                or any(c not in "0123456789abcdef" for c in expected_artifact_digest[7:])):
            raise RuntimeBundleReleaseRejected("expected artifact digest must use sha256:<64 lowercase hex>")
        bundle_bytes = Path(bundle_path).read_bytes()
        if not bundle_bytes:
            raise RuntimeBundleReleaseRejected("runtime bundle bytes must not be empty")
        actual_bundle_sha = hashlib.sha256(bundle_bytes).hexdigest()
        bundle_result = validate_runtime_bundle(bundle_path, expected_source_sha=expected_sha)
        if bundle_result["bundle_sha256"] != actual_bundle_sha:
            raise RuntimeBundleReleaseRejected("bundle digest changed while validating the release")
        attestation = load_runtime_bundle_attestation(attestation_path)
        if not trusted_public_keys:
            raise RuntimeBundleReleaseRejected('at least one trusted Ed25519 public key is required')
        verifier = Ed25519RuntimeBundleAttestationVerifier(
            trusted_public_keys, allowed_issuers=allowed_issuers, allowed_subjects=allowed_subjects,
            max_age_seconds=max_age_seconds, max_clock_skew_seconds=max_clock_skew_seconds,
        )
        if not verifier.verify(
            attestation, expected_bundle_sha256=actual_bundle_sha, expected_source_revision=expected_sha,
            expected_build_run_id=expected_build_run_id, expected_artifact_id=expected_artifact_id,
            expected_artifact_name=expected_artifact_name, expected_artifact_digest=expected_artifact_digest,
        ):
            raise RuntimeBundleReleaseRejected("runtime bundle attestation signature or provenance did not verify")
        return {
            "bundle_sha256": actual_bundle_sha, "source_revision": expected_sha,
            "build_run_id": expected_build_run_id, "artifact_id": expected_artifact_id,
            "artifact_name": expected_artifact_name, "artifact_digest": expected_artifact_digest,
            "issuer": attestation.issuer, "subject": attestation.subject,
            "files_verified": int(bundle_result["files_verified"]),
        }
    except RuntimeBundleReleaseRejected:
        raise
    except (OSError, ValueError, TypeError) as exc:
        raise RuntimeBundleReleaseRejected("runtime bundle release could not be validated") from exc
