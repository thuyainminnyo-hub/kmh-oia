"""Capture decision feedback as an observation or a verifier-gated learning candidate.

The feedback API intentionally does not accept caller-constructible admission
objects as proof of verification. The current milestone records caller-supplied
outcomes as provisional observations only; promotion requires a later trusted
service integration, not a boolean or dataclass passed by a caller.
"""
from dataclasses import dataclass

from src.adaptation_engine import AdaptationProposal
from src.decision_outcome_evaluator import DecisionOutcome
from src.operating_memory import OperatingMemory, OperatingMemoryRecord


@dataclass(frozen=True)
class DecisionLearningFeedback:
    outcome: DecisionOutcome
    memory: OperatingMemoryRecord
    adaptation: AdaptationProposal | None
    admission: None = None


class DecisionLearningFeedbackEngine:
    """Persist observations without allowing caller-controlled admission bypass."""

    def capture(
        self,
        outcome: DecisionOutcome,
        *,
        memory: OperatingMemory,
        wanted: str,
        actual: str,
        next_command: str,
        confidence: float = 1.0,
        pattern: str = "",
        proposed_change: str = "",
        expected_effect: str = "",
        next_experiment: str = "",
        admission=None,
    ) -> DecisionLearningFeedback:
        # This path does not yet possess a durable, non-forgeable admission
        # service result. Refuse any injected proof instead of trusting a
        # dataclass instance supplied by the caller.
        if admission is not None:
            raise ValueError(
                "caller-supplied admission objects are not trusted; "
                "use the trusted runtime admission service"
            )

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
        # Do not create an adaptation proposal here. Wiring a durable trusted
        # admission service into this API is a subsequent integration step.
        return DecisionLearningFeedback(outcome, record, None, None)
