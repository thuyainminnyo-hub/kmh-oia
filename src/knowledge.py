"""Deterministic knowledge retrieval boundary for KMH OIA integration."""

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class KnowledgeItem:
    source: str
    content: str


class KnowledgeSource(Protocol):
    """Boundary for retrieving relevant knowledge for a goal."""

    def retrieve(self, goal: str) -> list[KnowledgeItem]: ...


class StaticKnowledgeSource:
    """Small deterministic keyword-based knowledge source for integration tests."""

    def __init__(self, items: list[KnowledgeItem] | None = None) -> None:
        self._items = items or [
            KnowledgeItem("kmh-oia", "KMH OIA uses governed tools and structured runtime traces."),
            KnowledgeItem("stage-11", "Stage 11 integrates memory, knowledge, workflow, agents, tools, security, evaluation, and observability."),
        ]

    def retrieve(self, goal: str) -> list[KnowledgeItem]:
        normalized = goal.lower()
        matches = [item for item in self._items if any(word in item.content.lower() for word in normalized.split())]
        return matches
