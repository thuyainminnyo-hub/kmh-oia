"""Create an Ed25519-signed runtime artifact attestation from actual artifact bytes.

Private signing material is read only from KMH_OIA_ATTESTATION_PRIVATE_KEY_B64.
The secret must be provisioned by the protected release environment, never committed.
"""
from __future__ import annotations

import argparse
import base64
from datetime import datetime, timezone
import os
from pathlib import Path
import re
import sys
from typing import Mapping

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from src.runtime_artifact_attestation import RuntimeArtifactAttestation, canonical_attestation_payload
from src.runtime_artifact_io import RuntimeArtifactAttestationIOError, write_runtime_artifact_attestation
from src.runtime_artifact_measurement import measure_artifact


class RuntimeArtifactAttestationCreationError(ValueError):
    """Raised when release signing inputs are incomplete or invalid."""


def create_signed_runtime_attestation(
    classifier_path: str | Path,
    policy_path: str | Path,
    *,
    source_revision: str,
    build_run_id: str,
    environ: Mapping[str, str] | None = None,
) -> RuntimeArtifactAttestation:
    """Sign measured classifier/policy digests; never logs or persists private-key bytes."""
    env = os.environ if environ is None else environ
    private_key_b64 = env.get("KMH_OIA_ATTESTATION_PRIVATE_KEY_B64")
    if not isinstance(private_key_b64, str) or not private_key_b64.strip():
        raise RuntimeArtifactAttestationCreationError("KMH_OIA_ATTESTATION_PRIVATE_KEY_B64 is required")
    try:
        private_key_bytes = base64.b64decode(private_key_b64, validate=True)
    except (ValueError, TypeError) as exc:
        raise RuntimeArtifactAttestationCreationError("signing key must be valid base64") from exc
    if len(private_key_bytes) != 32:
        raise RuntimeArtifactAttestationCreationError("signing key must decode to 32 raw Ed25519 seed bytes")
    try:
        private_key = Ed25519PrivateKey.from_private_bytes(private_key_bytes)
    except ValueError as exc:
        raise RuntimeArtifactAttestationCreationError("Ed25519 signing key is invalid") from exc

    key_id = env.get("KMH_OIA_ATTESTATION_KEY_ID", "").strip()
    issuer = env.get("KMH_OIA_ATTESTATION_ISSUER", "").strip()
    subject = env.get("KMH_OIA_ATTESTATION_SUBJECT", "").strip()
    if any(not item or item == "*" for item in (key_id, issuer, subject)):
        raise RuntimeArtifactAttestationCreationError("key ID, issuer, and exact subject are required")
    if not isinstance(build_run_id, str) or not build_run_id.strip():
        raise RuntimeArtifactAttestationCreationError("build_run_id is required")
    source_revision = source_revision.strip().lower()
    if len(source_revision) not in (40, 64) or re.fullmatch(r"[0-9a-f]+", source_revision) is None:
        raise RuntimeArtifactAttestationCreationError("source_revision must be a full 40- or 64-character hexadecimal SHA")

    # Measure and validate artifacts before production run-context checks so failures
    # report the earliest actionable artifact issue deterministically.
    try:
        classifier = measure_artifact(classifier_path)
        policy = measure_artifact(policy_path)
    except Exception as exc:
        raise RuntimeArtifactAttestationCreationError("artifact bytes could not be measured") from exc
    if not classifier.content or not policy.content:
        raise RuntimeArtifactAttestationCreationError("classifier and policy artifacts must not be empty")

    # In production, the statement must be tied to the current GitHub Actions run context.
    # This is a defensive application check, not a replacement for protected environments or key custody.
    if env.get("KMH_OIA_ENVIRONMENT", "").strip().casefold() == "production":
        if env.get("GITHUB_ACTIONS", "").strip().lower() != "true":
            raise RuntimeArtifactAttestationCreationError("production signing requires the GitHub Actions runtime context")
        if env.get("GITHUB_SHA", "").strip().lower() != source_revision:
            raise RuntimeArtifactAttestationCreationError("source_revision must match the trusted GITHUB_SHA")
        if env.get("GITHUB_RUN_ID", "").strip() != build_run_id.strip():
            raise RuntimeArtifactAttestationCreationError("build_run_id must match the trusted GITHUB_RUN_ID")
        if env.get("GITHUB_REF", "").strip() != "refs/heads/main":
            raise RuntimeArtifactAttestationCreationError("production signing is allowed only from refs/heads/main")
        if env.get("GITHUB_EVENT_NAME", "").strip() != "workflow_dispatch":
            raise RuntimeArtifactAttestationCreationError("production signing requires a workflow_dispatch event")

    statement = RuntimeArtifactAttestation(
        classifier_sha256=classifier.sha256,
        policy_sha256=policy.sha256,
        issuer=issuer,
        subject=subject,
        attestation_id=f"{key_id}:{build_run_id.strip()}",
        key_id=key_id,
        source_revision=source_revision,
        build_run_id=build_run_id.strip(),
        issued_at=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        signature="",
        schema_version=1,
    )
    signature = private_key.sign(canonical_attestation_payload(statement))
    return RuntimeArtifactAttestation(
        **{
            **statement.__dict__,
            "signature": base64.b64encode(signature).decode("ascii"),
        }
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--classifier", required=True, help="path to the built classifier artifact")
    parser.add_argument("--policy", required=True, help="path to the built policy artifact")
    parser.add_argument("--source-revision", required=True, help="full Git source SHA from the trusted build context")
    parser.add_argument("--build-run-id", required=True, help="unique trusted CI/release run identifier")
    parser.add_argument("--output", required=True, help="new .json output path; existing files are never overwritten")
    args = parser.parse_args(argv)
    try:
        attestation = create_signed_runtime_attestation(
            args.classifier, args.policy,
            source_revision=args.source_revision,
            build_run_id=args.build_run_id,
        )
        write_runtime_artifact_attestation(args.output, attestation)
    except (RuntimeArtifactAttestationCreationError, RuntimeArtifactAttestationIOError) as exc:
        print(f"Runtime artifact attestation creation failed closed: {exc}", file=sys.stderr)
        return 2
    print(f"Signed runtime artifact attestation created: id={attestation.attestation_id}")
    print(f"classifier_sha256={attestation.classifier_sha256}")
    print(f"policy_sha256={attestation.policy_sha256}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
