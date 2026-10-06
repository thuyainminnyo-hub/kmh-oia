"""Structured trace record for the executable Operating Intelligence loop.

This record binds the implementation-side identifiers that must survive from
decision through execution, QA, evidence, and learning. It does not claim
external business validation; evidence status remains an explicit boundary.
"""

from dataclasses import dataclass
from typing import Literal


EvidenceStatus = Literal["UNKNOWN", "OBSERVED", "VERIFIED", "OUTCOME_LINKED"]
LearningStatus = Literal["NOT_ADMITTED", "ADMITTED"]


@dataclass(frozen=True)
class OperatingLoopRecord:
    """Traceable implementation record for one operating-loop execution."""

    context_id: str
    decision_id: str
    command_id: str
    execution_id: str
    trace_id: str
    qa_status: str
    evidence_status: EvidenceStatus
    learning_status: LearningStatus
    source_decision_id: str | None = None

    def __post_init__(self) -> None:
        required = {
            "context_id": self.context_id,
            "decision_id": self.decision_id,
            "command_id": self.command_id,
            "execution_id": self.execution_id,
            "trace_id": self.trace_id,
            "qa_status": self.qa_status,
        }
        missing = tuple(name for name, value in required.items() if not value.strip())
        if missing:
            raise ValueError("required operating-loop identifiers are missing: " + ", ".join(missing))

    @property
    def decision_traceable(self) -> bool:
        return self.source_decision_id == self.decision_id if self.source_decision_id else False

    @property
    def externally_validated(self) -> bool:
        return self.evidence_status == "OUTCOME_LINKED"
