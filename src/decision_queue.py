"""Convert intelligence signals into governed decision-queue items."""

from dataclasses import dataclass
from .telemetry_signal_engine import IntelligenceSignal


DecisionStatus = str


@dataclass(frozen=True)
class DecisionItem:
    id: str
    signal_kind: str
    severity: str
    problem: str
    recommended_action: str
    owner: str
    status: DecisionStatus = "PENDING"


class DecisionQueue:
    """Local-first queue for human/governed decisions raised by intelligence signals."""

    def __init__(self) -> None:
        self._items: list[DecisionItem] = []

    def enqueue(self, signal: IntelligenceSignal, *, owner: str) -> DecisionItem:
        if not owner.strip():
            raise ValueError("owner is required")
        item = DecisionItem(
            id=f"decision:{signal.kind.lower()}:{len(self._items) + 1}",
            signal_kind=signal.kind,
            severity=signal.severity,
            problem=signal.message,
            recommended_action=signal.recommended_action,
            owner=owner,
        )
        self._items.append(item)
        return item

    def pending(self) -> list[DecisionItem]:
        return [item for item in self._items if item.status == "PENDING"]

    def decide(self, decision_id: str, *, approved: bool) -> DecisionItem:
        for index, item in enumerate(self._items):
            if item.id == decision_id:
                status = "APPROVED" if approved else "REJECTED"
                updated = DecisionItem(
                    item.id, item.signal_kind, item.severity,
                    item.problem, item.recommended_action, item.owner, status
                )
                self._items[index] = updated
                return updated
        raise KeyError(decision_id)
