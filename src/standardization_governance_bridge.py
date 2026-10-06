"""Bridge proposed standards into explicit governance activation."""
from dataclasses import dataclass
from .standard_activation_control import ActivationResult, StandardActivationControl
from .standardization_engine import OperatingStandard

@dataclass(frozen=True)
class GovernanceReview:
    standard_id: str
    decision: str
    reason: str
    activation: ActivationResult | None

class StandardizationGovernanceBridge:
    """Keep standard proposal, approval, and activation as explicit governance steps."""
    def __init__(self, control=None):
        self.control = control or StandardActivationControl()

    def review(self, standard: OperatingStandard, *, approved: bool, reason: str = "") -> GovernanceReview:
        if not reason.strip():
            raise ValueError("governance reason is required")
        if standard.status != "PROPOSED":
            raise ValueError("only proposed standards can enter governance review")
        if not approved:
            return GovernanceReview(standard.id, "REJECTED", reason, None)
        activation = self.control.approve(standard)
        return GovernanceReview(standard.id, "APPROVED", reason, activation)

    def activate(self, review: GovernanceReview) -> ActivationResult:
        if review.decision != "APPROVED" or review.activation is None:
            raise ValueError("only approved governance reviews can activate a standard")
        return self.control.activate(review.activation.standard)
