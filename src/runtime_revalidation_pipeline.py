"""Automatic revalidation pipeline for live runtime standard feedback."""

from dataclasses import dataclass

from .standard_control_plane import StandardControlPlane, StandardControlResult
from .standardization_engine import OperatingStandard


@dataclass(frozen=True)
class AutomaticRevalidationResult:
    control_result: StandardControlResult
    revalidated: bool
    observed_effect: float | None
    outcome_positive: bool | None


class RuntimeRevalidationPipeline:
    """Turn drift feedback into governed revalidation without auto-activating changes."""

    def __init__(self, control_plane: StandardControlPlane | None = None) -> None:
        self.control_plane = control_plane or StandardControlPlane()

    def process(
        self,
        standard: OperatingStandard,
        command_id: str,
        *,
        applied_rule: str,
        evidence_id: str,
        observed_effect: float,
        outcome_positive: bool,
    ) -> AutomaticRevalidationResult:
        control = self.control_plane.observe(
            standard,
            command_id,
            applied_rule=applied_rule,
            evidence_id=evidence_id,
        )

        if control.trigger is None:
            return AutomaticRevalidationResult(
                control_result=control,
                revalidated=False,
                observed_effect=None,
                outcome_positive=None,
            )

        revalidated = self.control_plane.revalidate(
            control,
            standard,
            observed_effect=observed_effect,
            outcome_positive=outcome_positive,
        )
        return AutomaticRevalidationResult(
            control_result=revalidated,
            revalidated=True,
            observed_effect=observed_effect,
            outcome_positive=outcome_positive,
        )
