"""Stage 15 evidence closure gate.

This module turns the externally supplied P15.7 evidence bundle into a
deterministic closure check. It validates only supplied evidence; it does not
collect telemetry, execute drills, grant authorization, or certify production.
"""

from dataclasses import dataclass

from .p15_7_evidence import EvidenceBundle, EvidenceBundleBuilder


@dataclass(frozen=True)
class EvidenceClosure:
    release_id: str
    complete: bool
    missing: tuple[str, ...] = ()
    reason: str = ""


class EvidenceClosureController:
    """Require the declared external evidence categories for one release."""

    REQUIRED_NAMES = EvidenceBundleBuilder.REQUIRED_NAMES

    def evaluate(
        self,
        bundle: EvidenceBundle,
        *,
        expected_release_id: str,
    ) -> EvidenceClosure:
        if not isinstance(bundle, EvidenceBundle):
            raise ValueError("evidence bundle is required")
        release = expected_release_id.strip()
        if not release:
            raise ValueError("expected_release_id is required")
        if bundle.release_id != release:
            raise ValueError("evidence bundle release_id does not match expected release")

        names = {artifact.name for artifact in bundle.artifacts}
        missing = tuple(name for name in self.REQUIRED_NAMES if name not in names)
        if missing:
            return EvidenceClosure(
                release,
                False,
                missing,
                "evidence closure blocked: " + ", ".join(missing),
            )

        return EvidenceClosure(
            release,
            True,
            (),
            "all required external evidence categories are present",
        )

    def validate(self, state: EvidenceClosure) -> None:
        if not isinstance(state, EvidenceClosure):
            raise ValueError("evidence closure state is required")
        if not state.complete:
            raise RuntimeError(state.reason or "evidence closure is incomplete")
