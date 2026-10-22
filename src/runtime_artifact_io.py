"""Strict JSON serialization and parsing for signed runtime artifact attestations."""
from __future__ import annotations

from dataclasses import asdict
import json
from pathlib import Path

from src.runtime_artifact_attestation import RuntimeArtifactAttestation
from src.runtime_artifact_measurement import normalize_sha256


_ATTESTATION_FIELDS = frozenset({
    "classifier_sha256", "policy_sha256", "issuer", "subject", "attestation_id",
    "key_id", "source_revision", "build_run_id", "issued_at", "signature", "schema_version",
})


class RuntimeArtifactAttestationIOError(ValueError):
    """Raised when an attestation JSON document is malformed or cannot be safely written."""


def write_runtime_artifact_attestation(path: str | Path, attestation: RuntimeArtifactAttestation) -> Path:
    """Write a signed statement to a new JSON file; do not overwrite existing evidence."""
    if not isinstance(attestation, RuntimeArtifactAttestation):
        raise RuntimeArtifactAttestationIOError("a runtime artifact attestation object is required")
    destination = Path(path)
    if destination.suffix.lower() != ".json":
        raise RuntimeArtifactAttestationIOError("attestation output path must end in .json")
    payload = json.dumps(asdict(attestation), sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n"
    if len(payload.encode("utf-8")) > 65536:
        raise RuntimeArtifactAttestationIOError("attestation JSON exceeds 64 KiB")
    try:
        with destination.open("x", encoding="utf-8", newline="\n") as handle:
            handle.write(payload)
    except FileExistsError as exc:
        raise RuntimeArtifactAttestationIOError("attestation output already exists; refusing to overwrite evidence") from exc
    except OSError as exc:
        raise RuntimeArtifactAttestationIOError("attestation output could not be written") from exc
    return destination


def load_runtime_artifact_attestation(path: str | Path) -> RuntimeArtifactAttestation:
    """Strictly parse a JSON statement; cryptographic authentication remains verifier-owned."""
    source = Path(path)
    try:
        payload_bytes = source.read_bytes()
    except OSError as exc:
        raise RuntimeArtifactAttestationIOError("attestation file could not be read") from exc
    if not payload_bytes or len(payload_bytes) > 65536:
        raise RuntimeArtifactAttestationIOError("attestation file is empty or exceeds 64 KiB")
    try:
        data = json.loads(payload_bytes.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RuntimeArtifactAttestationIOError("attestation file must be valid UTF-8 JSON") from exc
    if not isinstance(data, dict) or frozenset(data) != _ATTESTATION_FIELDS:
        raise RuntimeArtifactAttestationIOError("attestation JSON must contain exactly the supported fields")
    if isinstance(data.get("schema_version"), bool) or data.get("schema_version") != 1:
        raise RuntimeArtifactAttestationIOError("unsupported attestation schema version")
    required_strings = _ATTESTATION_FIELDS - {"schema_version"}
    if any(not isinstance(data.get(field), str) or not data[field].strip() for field in required_strings):
        raise RuntimeArtifactAttestationIOError("attestation string fields must be non-empty strings")
    try:
        normalize_sha256(data["classifier_sha256"])
        normalize_sha256(data["policy_sha256"])
    except ValueError as exc:
        raise RuntimeArtifactAttestationIOError("attestation contains an invalid SHA-256 digest") from exc
    revision = data["source_revision"].lower()
    if len(revision) not in (40, 64) or any(char not in "0123456789abcdef" for char in revision):
        raise RuntimeArtifactAttestationIOError("attestation source revision must be a full 40- or 64-character hexadecimal SHA")
    data["source_revision"] = revision
    return RuntimeArtifactAttestation(**data)
