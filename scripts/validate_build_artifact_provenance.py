"""Fail-closed validation of a trusted build artifact provenance envelope.

This validates a metadata contract, not the actual GitHub run or artifact service.
Callers must independently fetch the run and artifact from GitHub, validate their
identity/status/digest, and pass the trusted observed values as expected inputs.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
_DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
_REQUIRED_KEYS = {
    "schema_version",
    "repository",
    "workflow_path",
    "run_id",
    "run_attempt",
    "run_conclusion",
    "source_sha",
    "artifact_id",
    "artifact_name",
    "artifact_digest",
    "producer_run_id",
}


class BuildArtifactProvenanceError(ValueError):
    """Raised when a build-artifact provenance envelope fails closed."""


def validate_build_artifact_provenance(
    payload: Any,
    *,
    expected_repository: str,
    allowed_workflow_paths: tuple[str, ...],
    expected_source_sha: str,
    expected_run_id: str,
    expected_artifact_id: str,
    expected_artifact_name: str,
    expected_artifact_digest: str,
) -> dict[str, Any]:
    """Validate exact provenance fields and equality with externally observed trusted metadata."""
    if not isinstance(payload, dict):
        raise BuildArtifactProvenanceError("provenance envelope must be a JSON object")
    if set(payload) != _REQUIRED_KEYS:
        missing = sorted(_REQUIRED_KEYS - set(payload))
        extra = sorted(set(payload) - _REQUIRED_KEYS)
        raise BuildArtifactProvenanceError(
            f"provenance envelope fields mismatch (missing={missing}, extra={extra})"
        )
    if isinstance(payload["schema_version"], bool) or payload["schema_version"] != 1:
        raise BuildArtifactProvenanceError("unsupported provenance schema_version")
    if not isinstance(expected_repository, str) or not expected_repository.strip():
        raise BuildArtifactProvenanceError("expected repository must be configured")
    if not isinstance(allowed_workflow_paths, tuple) or not allowed_workflow_paths:
        raise BuildArtifactProvenanceError("an explicit approved workflow-path allowlist is required")
    if any(not isinstance(path, str) or not path.startswith(".github/workflows/") for path in allowed_workflow_paths):
        raise BuildArtifactProvenanceError("allowed workflow paths must be explicit repository workflow paths")

    for field in ("repository", "workflow_path", "run_conclusion", "source_sha",
                  "run_id", "artifact_id", "artifact_name", "artifact_digest", "producer_run_id"):
        if not isinstance(payload[field], str) or not payload[field].strip():
            raise BuildArtifactProvenanceError(f"{field} must be a non-empty string")
    for field in ("run_attempt",):
        value = payload[field]
        if isinstance(value, bool) or not isinstance(value, int) or value < 1:
            raise BuildArtifactProvenanceError(f"{field} must be a positive integer")

    if payload["repository"] != expected_repository:
        raise BuildArtifactProvenanceError("repository does not match the configured trusted repository")
    if payload["workflow_path"] not in allowed_workflow_paths:
        raise BuildArtifactProvenanceError("workflow_path is not on the approved producer allowlist")
    if payload["run_conclusion"] != "success":
        raise BuildArtifactProvenanceError("producer run must have successful conclusion")
    if not _SHA_RE.fullmatch(payload["source_sha"]):
        raise BuildArtifactProvenanceError("source_sha must be a full lowercase 40-character Git SHA")
    if payload["source_sha"] != expected_source_sha:
        raise BuildArtifactProvenanceError("producer source SHA does not match the expected release SHA")
    if payload["run_id"] != expected_run_id or payload["producer_run_id"] != expected_run_id:
        raise BuildArtifactProvenanceError("run ID and producer_run_id must match the trusted producer run")
    if not payload["run_id"].isdigit() or payload["run_id"].startswith("0"):
        raise BuildArtifactProvenanceError("run_id must be a canonical positive decimal ID")
    if not payload["artifact_id"].isdigit() or payload["artifact_id"].startswith("0"):
        raise BuildArtifactProvenanceError("artifact_id must be a canonical positive decimal ID")
    if payload["artifact_id"] != expected_artifact_id:
        raise BuildArtifactProvenanceError("artifact ID does not match the trusted artifact service response")
    if payload["artifact_name"] != expected_artifact_name or not payload["artifact_name"].strip():
        raise BuildArtifactProvenanceError("artifact name does not match the configured exact artifact name")
    if not _DIGEST_RE.fullmatch(payload["artifact_digest"]):
        raise BuildArtifactProvenanceError("artifact_digest must use sha256:<64 lowercase hex characters>")
    if payload["artifact_digest"] != expected_artifact_digest:
        raise BuildArtifactProvenanceError("artifact digest does not match the trusted artifact service response")

    # Return a copy so callers do not accidentally mutate the input object.
    return dict(payload)


def validate_provenance_file(path: str | Path, **expected: Any) -> dict[str, Any]:
    source = Path(path)
    try:
        data = json.loads(source.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise BuildArtifactProvenanceError("provenance file is missing, unreadable, or invalid UTF-8 JSON") from exc
    return validate_build_artifact_provenance(data, **expected)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", help="provenance envelope JSON")
    parser.add_argument("--repository", required=True)
    parser.add_argument("--workflow-path", action="append", required=True,
                        help="approved producer workflow path; repeat to allow more than one")
    parser.add_argument("--source-sha", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--artifact-id", required=True)
    parser.add_argument("--artifact-name", required=True)
    parser.add_argument("--artifact-digest", required=True)
    args = parser.parse_args(argv)
    try:
        validate_provenance_file(
            args.path,
            expected_repository=args.repository,
            allowed_workflow_paths=tuple(args.workflow_path),
            expected_source_sha=args.source_sha,
            expected_run_id=args.run_id,
            expected_artifact_id=args.artifact_id,
            expected_artifact_name=args.artifact_name,
            expected_artifact_digest=args.artifact_digest,
        )
    except BuildArtifactProvenanceError as exc:
        print(f"build artifact provenance: rejected: {exc}", file=sys.stderr)
        return 1
    print("build artifact provenance envelope: contract checks passed; external run/artifact identity must already be verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
