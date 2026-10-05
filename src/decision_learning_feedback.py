"""Feed evaluated decision outcomes into operating memory and adaptation."""

from dataclasses import dataclass

from .adaptation_engine import AdaptationEngine, AdaptationProposal
from .decision_outcome_evaluator import DecisionOutcome
from .operating_memory import OperatingMemory, OperatingMemoryRecord


@dataclass(frozen=True)
class DecisionLearningFeedback:
    outcome: DecisionOutcome
    memory: OperatingMemoryRecord
    adaptation: AdaptationProposal | None


class DecisionLearningFeedbackEngine:
    """Persist decision outcomes and create governed changes for poor results."""

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
    ) -> DecisionLearningFeedback:
        learned = (
            "Reinforce the decision pattern because the verified outcome was positive."
            if outcome.quality == "GOOD"
            else "Investigate the decision pattern because the verified outcome was negative."
        )
        changed = (
            "Keep the decision rule unless new evidence contradicts it."
            if outcome.quality == "GOOD"
            else "Propose a governed adaptation before repeating the decision pattern."
        )
        record = memory.record(
            command_id=outcome.command_id,
            wanted=wanted,
            did=outcome.reason,
            actual=actual,
            verified="Execution reached LEARNED and the outcome was evaluated.",
            decision=f"Decision {outcome.decision_id}: {outcome.quality}",
            learned=learned,
            changed=changed,
            next_command=next_command,
            confidence=confidence,
        )
        adaptation = None
        if outcome.quality == "POOR":
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
        return DecisionLearningFeedback(outcome, record, adaptation)
