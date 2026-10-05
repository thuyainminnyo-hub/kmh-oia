"""Turn an approved adaptation into a concrete Command Center command."""
from dataclasses import dataclass

from src.adaptation_engine import AdaptationProposal
from src.live_operating_console import Command, LiveOperatingConsole

@dataclass(frozen=True)
class AppliedAdaptation:
    adaptation_id: str
    command_id: str
    expected_effect: str
    next_experiment: str

class AdaptationCommandBridge:
    def apply(self, console: LiveOperatingConsole, proposal: AdaptationProposal, *, owner: str = "system") -> AppliedAdaptation:
        if proposal.status != "APPROVED":
            raise ValueError("only approved adaptations can become commands")
        command = console.add_command(
            objective=proposal.proposed_change, priority="P2", owner=owner,
            expected_output=proposal.expected_effect, next_action=proposal.next_experiment,
        )
        return AppliedAdaptation(proposal.id, command.id, proposal.expected_effect, proposal.next_experiment)
