"""Select the current active standard for runtime execution."""

from dataclasses import dataclass

from .standard_registry import StandardVersionRegistry
from .standardization_engine import OperatingStandard


@dataclass(frozen=True)
class ActiveStandardSelection:
    source_adaptation_id: str
    standard: OperatingStandard


class ActiveStandardResolver:
    """Resolve exactly one active standard version before execution."""

    def __init__(self, registry: StandardVersionRegistry | None = None) -> None:
        self.registry = registry or StandardVersionRegistry()

    def register(self, standard: OperatingStandard) -> OperatingStandard:
        return self.registry.register(standard)

    def resolve(self, source_adaptation_id: str) -> ActiveStandardSelection:
        if not source_adaptation_id.strip():
            raise ValueError("source_adaptation_id is required")
        standard = self.registry.active(source_adaptation_id)
        if standard is None:
            raise LookupError(f"no active standard for {source_adaptation_id}")
        return ActiveStandardSelection(source_adaptation_id, standard)
