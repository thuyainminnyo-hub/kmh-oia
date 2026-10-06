"""Materialize anomaly-specific actions into governed INBOX commands."""
from dataclasses import dataclass
from .anomaly_action_engine import AnomalyAction
from .live_operating_console import Command, LiveOperatingConsole

@dataclass(frozen=True)
class AnomalyCommand:
    anomaly_action: AnomalyAction
    command: Command

class AnomalyCommandMaterializer:
    def materialize(self, anomaly_action: AnomalyAction, console: LiveOperatingConsole, *, owner: str, expected_output: str) -> AnomalyCommand:
        action = anomaly_action.next_action
        if action.kind == "NONE":
            raise ValueError("cannot materialize an undetected anomaly")
        result = console.add_command(
            objective=action.action,
            priority="P1" if action.priority <= 2 else "P2" if action.priority <= 5 else "P3",
            owner=owner,
            expected_output=expected_output,
            next_action=action.action,
            source_action_kind=action.kind,
            source_action_priority=action.priority,
            source_action_reason=action.reason,
        )
        return AnomalyCommand(anomaly_action, result)
