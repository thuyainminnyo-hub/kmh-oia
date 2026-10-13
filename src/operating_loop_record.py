"""Structured trace record for the executable Operating Intelligence loop.

This record binds implementation-side identifiers across decision, execution,
QA, evidence, learning admission, and any resulting decision change. It does not
claim external business validation; evidence status remains an explicit boundary.
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
    evidence_refs: tuple[str, ...] = ()
    learning_admission_id: str | None = None
    decision_change_id: str | None = None

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

        if any(not ref.strip() for ref in self.evidence_refs):
            raise ValueError("evidence_refs must not contain blank references")
        if len(set(self.evidence_refs)) != len(self.evidence_refs):
            raise ValueError("evidence_refs must be unique")

        if self.learning_status == "ADMITTED":
            if not self.evidence_refs:
                raise ValueError("admitted learning requires at least one evidence reference")
            if not self.learning_admission_id or not self.learning_admission_id.strip():
                raise ValueError("admitted learning requires learning_admission_id")

        if self.decision_change_id is not None:
            if not self.decision_change_id.strip():
                raise ValueError("decision_change_id must not be blank")
            if self.learning_status != "ADMITTED" or not self.learning_admission_id:
                raise ValueError("decision change requires admitted learning")

    @property
    def decision_traceable(self) -> bool:
        return self.source_decision_id == self.decision_id if self.source_decision_id else False

    @property
    def externally_validated(self) -> bool:
        return self.evidence_status == "OUTCOME_LINKED"
