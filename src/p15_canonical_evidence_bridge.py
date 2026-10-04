"""Canonical P15 evidence -> Stage 14 package bridge.

The adapter accepts only explicit identity, mapping, evidence-reference, and
boundary inputs. It does not infer release/deployment identity, manufacture
evidence, or certify production.
"""

from dataclasses import dataclass
import hashlib
import re

from .operational_evidence_package import (
    OperationalEvidencePackage,
    OperationalEvidencePackageBuilder,
)
from .p15_8_evidence_closure import EvidenceClosure


_SHA256 = re.compile(r"^[0-9a-fA-F]{64}$")


@dataclass(frozen=True)
class ReleaseDeploymentMapping:
    release_id: str
    deployment_id: str


@dataclass(frozen=True)
class EvidenceReference:
    reference_id: str
    environment: str
    observed_at: str
    source: str
    value: str


@dataclass(frozen=True)
class Stage14EvidenceMapping:
    field: str
    evidence_reference_ids: tuple[str, ...]
    applicability: str
    rationale: str


@dataclass(frozen=True)
class BridgeInput:
    release_id: str
    deployment_id: str
    release_deployment_mappings: tuple[ReleaseDeploymentMapping, ...]
    closure: EvidenceClosure
    evidence_references: tuple[EvidenceReference, ...]
    stage14_mapping: tuple[Stage14EvidenceMapping, ...]
    production_boundary_acknowledged: bool


class CanonicalEvidenceBridgeAdapter:
    """Construct a Stage 14 package only from explicit bridge inputs."""

    REQUIRED_FIELDS = OperationalEvidencePackageBuilder.REQUIRED_EVIDENCE

    def build_package(self, bridge: BridgeInput) -> OperationalEvidencePackage:
        self._validate_bridge_input(bridge)

        references = {ref.reference_id: ref for ref in bridge.evidence_references}
        evidence: dict[str, str] = {}
        for mapping in bridge.stage14_mapping:
            evidence[mapping.field] = self._serialize_mapping(mapping, references)

        package = OperationalEvidencePackageBuilder().build(
            deployment_id=bridge.deployment_id,
            evidence=evidence,
        )
        OperationalEvidencePackageBuilder().require_complete(package)
        return package

    def _validate_bridge_input(self, bridge: BridgeInput) -> None:
        if not isinstance(bridge, BridgeInput):
            raise ValueError("bridge input is required")
        release = bridge.release_id.strip()
        deployment = bridge.deployment_id.strip()
        if not release:
            raise ValueError("release_id is required")
        if not deployment:
            raise ValueError("deployment_id is required")
        if not isinstance(bridge.production_boundary_acknowledged, bool):
            raise ValueError("production boundary acknowledgement must be boolean")
        if not bridge.production_boundary_acknowledged:
            raise RuntimeError("bridge blocked: production-boundary acknowledgement is required")

        closure = bridge.closure
        if not isinstance(closure, EvidenceClosure):
            raise ValueError("evidence closure is required")
        if closure.release_id != release:
            raise ValueError("evidence closure release_id does not match bridge release_id")
        if not closure.complete:
            raise RuntimeError("bridge blocked: evidence closure is incomplete")

        mappings = bridge.release_deployment_mappings
        if len(mappings) != 1:
            raise RuntimeError(
                "bridge blocked: exactly one explicit release-to-deployment mapping is required"
            )
        if not isinstance(mappings[0], ReleaseDeploymentMapping):
            raise ValueError("release-to-deployment mappings must contain valid mapping values")
        identity = mappings[0]
        if identity.release_id.strip() != release:
            raise ValueError("release-to-deployment mapping release_id does not match")
        if identity.deployment_id.strip() != deployment:
            raise ValueError("release-to-deployment mapping deployment_id does not match")

        refs = bridge.evidence_references
        if any(not isinstance(ref, EvidenceReference) for ref in refs):
            raise ValueError("evidence references must contain EvidenceReference values")
        reference_ids = [ref.reference_id for ref in refs]
        if len(set(reference_ids)) != len(reference_ids):
            raise ValueError("duplicate evidence reference id")
        if any(
            not isinstance(value, str) or not value.strip()
            for ref in refs
            for value in (
                ref.reference_id,
                ref.environment,
                ref.observed_at,
                ref.source,
                ref.value,
            )
        ):
            raise ValueError("evidence references require attributable provenance")

        mappings14 = bridge.stage14_mapping
        if any(not isinstance(mapping, Stage14EvidenceMapping) for mapping in mappings14):
            raise ValueError("Stage 14 mappings must contain valid mapping values")
        stage14_fields = [mapping.field for mapping in mappings14]
        if len(stage14_fields) != len(set(stage14_fields)):
            raise ValueError("duplicate Stage 14 evidence mapping field")
        unsupported = tuple(field for field in stage14_fields if field not in self.REQUIRED_FIELDS)
        if unsupported:
            raise RuntimeError(
                "bridge blocked: unsupported Stage 14 evidence fields: " + ", ".join(unsupported)
            )
        missing = tuple(field for field in self.REQUIRED_FIELDS if field not in stage14_fields)
        if missing:
            raise RuntimeError(
                "bridge blocked: missing Stage 14 evidence mappings: " + ", ".join(missing)
            )

        known_refs = set(reference_ids)
        for mapping in mappings14:
            if not mapping.evidence_reference_ids:
                raise RuntimeError(
                    f"bridge blocked: no evidence reference supplied for {mapping.field}"
                )
            if not mapping.applicability.strip() or not mapping.rationale.strip():
                raise RuntimeError(
                    f"bridge blocked: applicability/rationale required for {mapping.field}"
                )
            unknown = tuple(
                ref_id for ref_id in mapping.evidence_reference_ids if ref_id not in known_refs
            )
            if unknown:
                raise RuntimeError(
                    f"bridge blocked: unknown evidence reference(s) for {mapping.field}: "
                    + ", ".join(unknown)
                )

    @staticmethod
    def _serialize_mapping(
        mapping: Stage14EvidenceMapping,
        references: dict[str, EvidenceReference],
    ) -> str:
        parts = [
            f"field={mapping.field}",
            f"applicability={mapping.applicability.strip()}",
            f"rationale={mapping.rationale.strip()}",
        ]
        for ref_id in mapping.evidence_reference_ids:
            ref = references[ref_id]
            parts.append(
                "reference="
                + "|".join(
                    (
                        ref.reference_id.strip(),
                        ref.environment.strip(),
                        ref.observed_at.strip(),
                        ref.source.strip(),
                        ref.value.strip(),
                    )
                )
            )
        return ";".join(parts)


def verify_sha256(content: bytes, expected_sha256: str) -> bool:
    """Verify supplied-byte integrity only; this does not establish authenticity."""
    if not isinstance(content, bytes):
        raise TypeError("content must be bytes")
    if not isinstance(expected_sha256, str) or not _SHA256.fullmatch(expected_sha256):
        raise ValueError("expected_sha256 must be a 64-character hexadecimal digest")
    return hashlib.sha256(content).hexdigest().lower() == expected_sha256.lower()
