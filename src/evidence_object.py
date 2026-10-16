"""Immutable evidence-object contract for the KMH OIA operating loop.

This module validates provenance and evidence-state claims. It does not fetch or
verify external artifacts, establish business outcomes, or admit learning.
"""
from dataclasses import dataclass
from datetime import datetime
import re
from typing import Literal


EvidenceValidationState = Literal["OBSERVED", "VERIFIED", "OUTCOME_LINKED"]
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


@dataclass(frozen=True)
class EvidenceObject:
    """A single immutable reference to an observation and its provenance.

    Supply an artifact_ref or sha256_digest (or both). The validator checks
    identifier shape and state prerequisites only; callers must not interpret
    construction as proof that an artifact exists or that a claim is true.
    """

    evidence_id: str
    kind: str
    source: str
    observed_at: str
    scope: str
    source_revision: str
    artifact_ref: str | None = None
    sha256_digest: str | None = None
    run_id: str | None = None
    command_id: str | None = None
    trace_id: str | None = None
    execution_id: str | None = None
    config_version: str | None = None
    agent_version: str | None = None
    validation_state: EvidenceValidationState = "OBSERVED"
    validation_ref: str | None = None
    outcome_ref: str | None = None

    def __post_init__(self) -> None:
        required = {
            "evidence_id": self.evidence_id,
            "kind": self.kind,
            "source": self.source,
            "observed_at": self.observed_at,
            "scope": self.scope,
            "source_revision": self.source_revision,
        }
        missing = [name for name, value in required.items()
                   if not isinstance(value, str) or not value.strip()]
        if missing:
            raise ValueError("required evidence fields are missing: " + ", ".join(missing))

        try:
            parsed = datetime.fromisoformat(
                self.observed_at[:-1] + "+00:00"
                if self.observed_at.endswith("Z") else self.observed_at
            )
        except ValueError as exc:
            raise ValueError("observed_at must be an ISO-8601 timestamp") from exc
        if parsed.tzinfo is None or parsed.utcoffset() is None:
            raise ValueError("observed_at must include a timezone offset")

        execution_refs = (self.run_id, self.command_id, self.trace_id, self.execution_id)
        if not any(isinstance(value, str) and value.strip() for value in execution_refs):
            raise ValueError("at least one execution reference is required")
        for name, value in (
            ("run_id", self.run_id),
            ("command_id", self.command_id),
            ("trace_id", self.trace_id),
            ("execution_id", self.execution_id),
            ("artifact_ref", self.artifact_ref),
            ("config_version", self.config_version),
            ("agent_version", self.agent_version),
            ("validation_ref", self.validation_ref),
            ("outcome_ref", self.outcome_ref),
        ):
            if value is not None and (not isinstance(value, str) or not value.strip()):
                raise ValueError(f"{name} must be a nonblank string when supplied")

        if not (self.artifact_ref or self.sha256_digest):
            raise ValueError("artifact_ref or sha256_digest is required")
        if self.sha256_digest is not None and (
            not isinstance(self.sha256_digest, str)
            or not _SHA256_RE.fullmatch(self.sha256_digest)
        ):
            raise ValueError("sha256_digest must be 64 lowercase hexadecimal characters")

        if self.validation_state not in ("OBSERVED", "VERIFIED", "OUTCOME_LINKED"):
            raise ValueError("unsupported validation_state")
        if self.validation_state in ("VERIFIED", "OUTCOME_LINKED"):
            if not self.validation_ref:
                raise ValueError("validation_ref is required for VERIFIED or OUTCOME_LINKED evidence")
        if self.validation_state == "OUTCOME_LINKED":
            if not self.outcome_ref:
                raise ValueError("outcome_ref is required for OUTCOME_LINKED evidence")
