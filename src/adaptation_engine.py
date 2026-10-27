"""Adaptation engine for converting operating memory into governed change proposals.

The engine proposes changes; it does not silently apply them. Approval remains
an explicit boundary before a proposal can become an active system change.
"""
from dataclasses import dataclass
from typing import Literal

from src.adaptation_proposal_repository import SQLiteAdaptationProposalRepository
from src.operating_memory import OperatingMemory, OperatingMemoryRecord

AdaptationStatus = Literal["PROPOSED", "APPROVED", "REJECTED", "APPLIED"]


@dataclass(frozen=True)
class AdaptationProposal:
    id: str
    source_command_id: str
    pattern: str
    problem: str
    proposed_change: str
    expected_effect: str
    next_experiment: str
    confidence: float
    status: AdaptationStatus = "PROPOSED"


class AdaptationEngine:
    """Generate explicit, reviewable adaptation proposals.

    When a durable repository is configured, proposal identity and governance
    status are recovered from storage on retries. Without one, behavior remains
    process-local for backwards compatibility and tests.
    """

    def __init__(
        self,
        repository: SQLiteAdaptationProposalRepository | None = None,
    ) -> None:
        self._repository = repository

    def propose(
        self,
        record: OperatingMemoryRecord,
        *,
        pattern: str,
        problem: str,
        proposed_change: str,
        expected_effect: str,
        next_experiment: str,
    ) -> AdaptationProposal:
        values = {
            "pattern": pattern,
            "problem": problem,
            "proposed_change": proposed_change,
            "expected_effect": expected_effect,
            "next_experiment": next_experiment,
        }
        for name, value in values.items():
            if not value.strip():
                raise ValueError(f"{name} is required")
        proposal = AdaptationProposal(
            id=f"adapt:{record.event_id or record.command_id}",
            source_command_id=record.command_id,
            **{name: value.strip() for name, value in values.items()},
            confidence=record.confidence,
        )
        if self._repository is None:
            return proposal
        canonical = self._repository.get_or_create(proposal, idempotency_key=proposal.id)
        return AdaptationProposal(**canonical)

    def from_memory(
        self,
        memory: OperatingMemory,
        *,
        query: str,
        pattern: str,
        problem: str,
        proposed_change: str,
        expected_effect: str,
        next_experiment: str,
    ) -> tuple[AdaptationProposal, ...]:
        records = memory.search(query)
        return tuple(
            self.propose(
                record,
                pattern=pattern,
                problem=problem,
                proposed_change=proposed_change,
                expected_effect=expected_effect,
                next_experiment=next_experiment,
            )
            for record in records
        )

    def _transition(self, proposal: AdaptationProposal, status: AdaptationStatus) -> AdaptationProposal:
        if self._repository is None:
            return AdaptationProposal(**{**proposal.__dict__, "status": status})
        canonical = self._repository.update_status(proposal.id, status)
        return AdaptationProposal(**canonical)

    def approve(self, proposal: AdaptationProposal) -> AdaptationProposal:
        if proposal.status != "PROPOSED":
            raise ValueError("only proposed adaptations can be approved")
        return self._transition(proposal, "APPROVED")

    def reject(self, proposal: AdaptationProposal) -> AdaptationProposal:
        if proposal.status != "PROPOSED":
            raise ValueError("only proposed adaptations can be rejected")
        return self._transition(proposal, "REJECTED")

    def apply(self, proposal: AdaptationProposal) -> AdaptationProposal:
        if proposal.status != "APPROVED":
            raise ValueError("only approved adaptations can be applied")
        return self._transition(proposal, "APPLIED")
