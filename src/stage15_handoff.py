"""Stage 14 deterministic Stage 15 handoff controller."""
from dataclasses import dataclass

from .operational_evidence_package import OperationalEvidencePackage


@dataclass(frozen=True)
class Stage15Handoff:
    deployment_id: str
    phase: str
    ready: bool
    evidence_complete: bool
    production_boundary_acknowledged: bool
    reason: str = ""


class Stage15HandoffController:
    """Gate Stage 15 handoff on explicit evidence and boundary acknowledgement."""

    def prepare(
        self,
        package: OperationalEvidencePackage,
        *,
        production_boundary_acknowledged: bool,
    ) -> Stage15Handoff:
        if not isinstance(package, OperationalEvidencePackage):
            raise ValueError("operational evidence package is required")
        if not isinstance(production_boundary_acknowledged, bool):
            raise ValueError("production boundary acknowledgement must be boolean")
        evidence_complete = package.complete and not package.missing
        acknowledged = production_boundary_acknowledged
        if not evidence_complete or not acknowledged:
            missing = []
            if not evidence_complete:
                missing.append("complete operational evidence package")
            if not acknowledged:
                missing.append("production-boundary acknowledgement")
            return Stage15Handoff(
                package.deployment_id, "blocked", False,
                evidence_complete, acknowledged,
                "handoff blocked: " + ", ".join(missing),
            )
        return Stage15Handoff(
            package.deployment_id, "ready", True, True, True,
            "Stage 15 handoff prerequisites satisfied; production execution is not certified",
        )

    def validate(self, state: Stage15Handoff) -> None:
        if state.phase != "ready" or not state.ready:
            raise RuntimeError("Stage 15 handoff is not ready")
        if not state.evidence_complete or not state.production_boundary_acknowledged:
            raise RuntimeError("Stage 15 handoff prerequisites are incomplete")
