"""Materialize a recommended next action as a governed Command."""

from dataclasses import dataclass

from .live_operating_console import Command, LiveOperatingConsole
from .next_action_engine import NextAction


@dataclass(frozen=True)
class MaterializedAction:
    action: NextAction
    command: Command


class NextActionCommandMaterializer:
    """Turn recommendations into INBOX commands while preserving provenance."""

    def materialize(
        self,
        action: NextAction,
        console: LiveOperatingConsole,
        *,
        owner: str,
        expected_output: str,\n        source_decision_id: str | None = None,
    ) -> MaterializedAction:
        if action.kind == "NONE":
            raise ValueError("cannot materialize an empty next action")
        if not owner.strip():
            raise ValueError("owner is required")
        if not expected_output.strip():
            raise ValueError("expected_output is required")
        priority = "P1" if action.priority <= 2 else "P2" if action.priority <= 5 else "P3"
        command = console.add_command(
            objective=action.action,
            priority=priority,
            owner=owner,
            expected_output=expected_output,
            next_action=action.action,
            source_action_kind=action.kind,
            source_action_priority=action.priority,
            source_action_reason=action.reason,\n            source_decision_id=source_decision_id,
        )
        return MaterializedAction(action, command)
