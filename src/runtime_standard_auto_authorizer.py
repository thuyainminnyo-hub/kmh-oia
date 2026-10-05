"""Resolve and enforce the active standard for a live command."""

from dataclasses import dataclass

from .active_standard_resolver import ActiveStandardResolver
from .standard_runtime_bridge import RuntimeStandardCheck


@dataclass(frozen=True)
class AutoAuthorization:
    command_id: str
    source_adaptation_id: str
    standard_id: str
    check: RuntimeStandardCheck


class RuntimeStandardAutoAuthorizer:
    """Select the active version and authorize a command before execution."""

    def __init__(self, resolver=None, runtime_bridge=None) -> None:
        self.resolver = resolver or ActiveStandardResolver()
        self.runtime_bridge = runtime_bridge

    def authorize(self, source_adaptation_id: str, command_id: str, *, applied_rule: str) -> AutoAuthorization:
        selection = self.resolver.resolve(source_adaptation_id)
        if self.runtime_bridge is None:
            from .standard_runtime_bridge import StandardRuntimeBridge
            bridge = StandardRuntimeBridge()
        else:
            bridge = self.runtime_bridge
        check = bridge.authorize(
            selection.standard,
            command_id,
            applied_rule=applied_rule,
        )
        return AutoAuthorization(
            command_id,
            source_adaptation_id,
            selection.standard.id,
            check,
        )
