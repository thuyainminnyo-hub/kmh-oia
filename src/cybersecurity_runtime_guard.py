"""Trusted adapter from live runtime commands to the cybersecurity registry.

The resolver must be supplied by trusted application code. It must derive
(case_id, version, action) from authenticated command metadata, never from free
text objectives or caller-supplied record dictionaries.
"""
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from scripts.cybersecurity_registry import authorize_execution, read_entries


def build_registry_execution_guard(
    registry_path: str | Path,
    resolve_request: Callable[[object], tuple[str, int, str]],
    *,
    clock: Callable[[], datetime] | None = None,
) -> Callable[[object], tuple[bool, str]]:
    """Create a fail-closed guard resolving an exact registry case/version.

    resolve_request must be trusted application code and return case ID,
    immutable version number, and action. The full hash chain is checked on
    every call. This guard authorizes the command boundary; it does not itself
    perform remediation or replace executor-level least-privilege checks.
    """
    def guard(command: object) -> tuple[bool, str]:
        if getattr(command, "source_action_kind", None) != "cybersecurity_remediation":
            return True, "not a cybersecurity remediation command"
        try:
            case_id, version, action = resolve_request(command)
            if not isinstance(case_id, str) or not case_id:
                return False, "trusted resolver returned an invalid case ID"
            if not isinstance(version, int) or isinstance(version, bool) or version < 1:
                return False, "trusted resolver returned an invalid registry version"
            if not isinstance(action, str) or not action:
                return False, "trusted resolver returned an invalid action"
            entries = read_entries(registry_path)
            matches = [
                entry for entry in entries
                if entry.get("case_id") == case_id and entry.get("version") == version
            ]
            if len(matches) != 1:
                return False, "exact registry case/version not found"
            now = clock() if clock is not None else datetime.now(timezone.utc)
            allowed, reason = authorize_execution(matches[0]["record"], action, now=now)
            return allowed, reason
        except Exception as exc:
            return False, f"cybersecurity registry guard failed closed: {type(exc).__name__}: {exc}"

    return guard
