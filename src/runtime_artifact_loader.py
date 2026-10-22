"""Verify signed artifact provenance before loading the exact measured byte payloads.

The caller supplies format-specific loaders. They receive immutable bytes that were
measured and verified; they must not reopen a mutable path to re-load the artifact.
This module does not provide a build signer or provision production trust keys.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Generic, TypeVar
import hashlib

from src.runtime_artifact_attestation import RuntimeArtifactAttestation, RuntimeArtifactAttestationVerifier
from src.runtime_artifact_measurement import measure_artifact, normalize_sha256

T = TypeVar("T")
U = TypeVar("U")


class RuntimeArtifactLoadError(RuntimeError):
    """Raised when provenance validation or format-specific loading fails."""


@dataclass(frozen=True)
class VerifiedRuntimeArtifacts(Generic[T, U]):
    """Bundle of loader outputs and the exact measured bytes used to construct them."""
    classifier: T
    policy: U
    classifier_bytes: bytes
    policy_bytes: bytes
    classifier_sha256: str
    policy_sha256: str
    attestation: RuntimeArtifactAttestation
    verifier: RuntimeArtifactAttestationVerifier

    def verify_integrity(self) -> bool:
        """Re-measure stored immutable payloads and re-authenticate their attestation."""
        try:
            if not isinstance(self.classifier_bytes, bytes) or not self.classifier_bytes:
                return False
            if not isinstance(self.policy_bytes, bytes) or not self.policy_bytes:
                return False
            classifier_digest = hashlib.sha256(self.classifier_bytes).hexdigest()
            policy_digest = hashlib.sha256(self.policy_bytes).hexdigest()
            if classifier_digest != normalize_sha256(self.classifier_sha256):
                return False
            if policy_digest != normalize_sha256(self.policy_sha256):
                return False
            return self.verifier.verify(
                self.attestation, expected_classifier_sha256=classifier_digest,
                expected_policy_sha256=policy_digest,
            ) is True
        except Exception:
            return False


def verify_and_load_runtime_artifacts_from_bytes(
    classifier_bytes: bytes,
    policy_bytes: bytes,
    *,
    attestation: RuntimeArtifactAttestation,
    verifier: RuntimeArtifactAttestationVerifier,
    classifier_loader: Callable[[bytes], T],
    policy_loader: Callable[[bytes], U],
) -> VerifiedRuntimeArtifacts[T, U]:
    """Verify actual byte digests and signed provenance before invoking either loader."""
    if not isinstance(classifier_bytes, bytes) or not classifier_bytes:
        raise RuntimeArtifactLoadError("classifier artifact bytes are missing or invalid")
    if not isinstance(policy_bytes, bytes) or not policy_bytes:
        raise RuntimeArtifactLoadError("policy artifact bytes are missing or invalid")
    if not callable(classifier_loader) or not callable(policy_loader):
        raise RuntimeArtifactLoadError("both artifact loaders must be callable")
    classifier_payload = bytes(classifier_bytes)
    policy_payload = bytes(policy_bytes)
    classifier_digest = hashlib.sha256(classifier_payload).hexdigest()
    policy_digest = hashlib.sha256(policy_payload).hexdigest()
    try:
        accepted = verifier.verify(
            attestation, expected_classifier_sha256=classifier_digest,
            expected_policy_sha256=policy_digest,
        )
    except Exception as exc:
        raise RuntimeArtifactLoadError("runtime artifact provenance verification failed") from exc
    if accepted is not True:
        raise RuntimeArtifactLoadError("runtime artifact provenance verification failed closed")
    # Do not call format loaders until signature and actual-byte digest checks pass.
    try:
        classifier = classifier_loader(classifier_payload)
        policy = policy_loader(policy_payload)
    except Exception as exc:
        raise RuntimeArtifactLoadError("verified artifact loading failed") from exc
    if classifier is None or policy is None:
        raise RuntimeArtifactLoadError("artifact loader returned an empty runtime object")
    bundle = VerifiedRuntimeArtifacts(
        classifier=classifier, policy=policy, classifier_bytes=classifier_payload,
        policy_bytes=policy_payload, classifier_sha256=classifier_digest,
        policy_sha256=policy_digest, attestation=attestation, verifier=verifier,
    )
    if not bundle.verify_integrity():
        raise RuntimeArtifactLoadError("loaded runtime artifact bundle integrity check failed")
    return bundle


def verify_and_load_runtime_artifacts(
    classifier_path: str | Path,
    policy_path: str | Path,
    *,
    attestation: RuntimeArtifactAttestation,
    verifier: RuntimeArtifactAttestationVerifier,
    classifier_loader: Callable[[bytes], T],
    policy_loader: Callable[[bytes], U],
) -> VerifiedRuntimeArtifacts[T, U]:
    """Read each path once, then verify and load the exact measured bytes."""
    try:
        classifier_artifact = measure_artifact(classifier_path)
        policy_artifact = measure_artifact(policy_path)
    except Exception as exc:
        raise RuntimeArtifactLoadError("runtime artifact bytes could not be measured") from exc
    if not classifier_artifact.content or not policy_artifact.content:
        raise RuntimeArtifactLoadError("runtime artifact files must not be empty")
    # Delegate using the byte snapshots; loaders never receive/reopen the paths.
    return verify_and_load_runtime_artifacts_from_bytes(
        classifier_artifact.content, policy_artifact.content,
        attestation=attestation, verifier=verifier,
        classifier_loader=classifier_loader, policy_loader=policy_loader,
    )
