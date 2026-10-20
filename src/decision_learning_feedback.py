"""Feed evaluated outcomes into memory, qualifying learning only with admitted evidence."""
from dataclasses import dataclass

from src.adaptation_engine import AdaptationEngine, AdaptationProposal
from src.decision_outcome_evaluator import DecisionOutcome
from src.operating_memory import OperatingMemory, OperatingMemoryRecord
from src.verified_learning_admission import VerifiedLearningAdmission


@dataclass(frozen=True)
class DecisionLearningFeedback:
    outcome: DecisionOutcome
    memory: OperatingMemoryRecord
    adaptation: AdaptationProposal | None
    admission: VerifiedLearningAdmission | None = None


class DecisionLearningFeedbackEngine:
    """Persist observations; create adaptation proposals only after evidence admission."""

    def capture(
        self,
        outcome: DecisionOutcome,
        *,
        memory: OperatingMemory,
        wanted: str,
        actual: str,
        next_command: str,
        confidence: float = 1.0,
        adaptation_engine: AdaptationEngine | None = None,
        pattern: str = "",
        proposed_change: str = "",
        expected_effect: str = "",
        next_experiment: str = "",
        admission: VerifiedLearningAdmission | None = None,
    ) -> DecisionLearningFeedback:
        if admission is not None:
            if not isinstance(admission, VerifiedLearningAdmission):
                raise ValueError("admission must be a VerifiedLearningAdmission")
            if (
                admission.decision_id != outcome.decision_id
                or admission.command_id != outcome.command_id
            ):
                raise ValueError("learning admission does not match the decision outcome")

        admitted = admission is not None
        if admitted:
            learned = (
                "Outcome-linked evidence was admitted; retain the result for governed learning review."
                if outcome.quality == "GOOD"
                else "Outcome-linked evidence was admitted; investigate the poor result through governed adaptation review."
            )
            changed = (
                "Keep the decision rule unless new admitted evidence contradicts it."
                if outcome.quality == "GOOD"
                else "Prepare a governed adaptation proposal; approval is still required before application."
            )
            verified = (
                "Trusted source receipt passed runtime verification and outcome-linked evidence admission; "
                "this does not independently prove causality beyond the linked records."
            )
        else:
            learned = (
                "Store as a provisional observation only; trusted external outcome evidence has not been admitted."
            )
            changed = (
                "Do not promote or reinforce a decision rule from this observation alone."
                if outcome.quality == "GOOD"
                else "Hold adaptation proposal creation until trusted outcome evidence is admitted."
            )
            verified = (
                "Caller-supplied outcome evaluation only; external source authenticity, attribution, "
                "and outcome verification are not established."
            )

        record = memory.record(
            command_id=outcome.command_id,
            wanted=wanted,
            did=outcome.reason,
            actual=actual,
            verified=verified,
            decision=f"Decision {outcome.decision_id}: {outcome.quality}",
            learned=learned,
            changed=changed,
            next_command=next_command,
            confidence=confidence,
        )
        adaptation = None
        if outcome.quality == "POOR" and admitted:
            if adaptation_engine is None:
                adaptation_engine = AdaptationEngine()
            adaptation = adaptation_engine.propose(
                record,
                pattern=pattern or f"decision:{outcome.decision_id}",
                problem=outcome.reason,
                proposed_change=proposed_change or "Review and improve the decision rule.",
                expected_effect=expected_effect or "Improve the next decision outcome.",
                next_experiment=next_experiment or next_command,
            )
        return DecisionLearningFeedback(outcome, record, adaptation, admission)
