"""Governed activation control for versioned operating standards."""

from dataclasses import dataclass

from .standard_registry import StandardVersionRegistry
from .standardization_engine import OperatingStandard, StandardizationEngine


@dataclass(frozen=True)
class ActivationResult:
    standard: OperatingStandard
    approved: bool
    activated: bool


class StandardActivationControl:
    """Approve and activate proposed standards without bypassing governance."""

    def __init__(self, registry=None, standardization=None):
        self.registry = registry or StandardVersionRegistry()
        self.standardization = standardization or StandardizationEngine()

    def approve(self, standard: OperatingStandard) -> ActivationResult:
        approved = self.standardization.approve(standard)
        self.registry.register(approved)
        return ActivationResult(approved, True, False)

    def activate(self, standard: OperatingStandard) -> ActivationResult:
        if standard.status != "APPROVED":
            raise ValueError("only approved standards can be activated")
        active = self.registry.active(standard.source_adaptation_id)
        if active is not None and active.id != standard.id:
            raise ValueError("an active standard version already exists")
        activated = self.standardization.activate(standard)
        self.registry.register(activated)
        return ActivationResult(activated, True, True)

    def approve_and_activate(self, standard: OperatingStandard) -> ActivationResult:
        approved = self.approve(standard).standard
        return self.activate(approved)

    def active(self, source_adaptation_id: str):
        return self.registry.active(source_adaptation_id)
