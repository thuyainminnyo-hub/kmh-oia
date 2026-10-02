"""Stage 15 reproducible operational evidence bundle.

This module validates the shape and provenance of externally supplied evidence.
It does not collect live telemetry, assert production execution, or authorize
deployment.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class EvidenceArtifact:
    name: str
    environment: str
    observed_at: str
    source: str
    value: str


@dataclass(frozen=True)
class EvidenceBundle:
    release_id: str
    artifacts: tuple[EvidenceArtifact, ...]


class EvidenceBundleBuilder:
    """Build a reproducible evidence bundle from explicitly supplied artifacts."""

    REQUIRED_NAMES = (
        "telemetry",
        "performance",
        "rollback_drill",
        "authorization",
        "incident_exercise",
    )

    def build(
        self,
        *,
        release_id: str,
        artifacts: tuple[EvidenceArtifact, ...],
    ) -> EvidenceBundle:
        release = release_id.strip()
        if not release:
            raise ValueError("release_id is required")
        if not artifacts:
            raise ValueError("at least one evidence artifact is required")

        seen: set[str] = set()
        for artifact in artifacts:
            if not isinstance(artifact, EvidenceArtifact):
                raise ValueError("artifacts must contain EvidenceArtifact values")
            fields = (
                artifact.name,
                artifact.environment,
                artifact.observed_at,
                artifact.source,
                artifact.value,
            )
            if any(not isinstance(field, str) or not field.strip() for field in fields):
                raise ValueError("evidence artifacts require non-empty provenance fields")
            if artifact.name in seen:
                raise ValueError("duplicate evidence artifact name")
            seen.add(artifact.name)

        return EvidenceBundle(release, tuple(artifacts))

    def require_names(
        self, bundle: EvidenceBundle, required: tuple[str, ...] | None = None
    ) -> None:
        names = required or self.REQUIRED_NAMES
        missing = tuple(name for name in names if name not in {a.name for a in bundle.artifacts})
        if missing:
            raise RuntimeError("evidence bundle incomplete: " + ", ".join(missing))
