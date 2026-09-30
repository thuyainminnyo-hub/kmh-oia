"""Typed governed-tool contracts for the KMH OIA runtime."""

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class ToolRequest:
    tool_name: str
    input_text: str


@dataclass(frozen=True)
class ToolResult:
    tool_name: str
    output_text: str
    success: bool
    reason: str


class ToolExecutor(Protocol):
    """Execution boundary consumed by the governed-tool component."""

    def execute(self, request: ToolRequest) -> ToolResult: ...


class ToolRegistry:
    """Small deterministic registry for executable governed tools."""

    def __init__(self) -> None:
        self._tools = {"echo": self._echo}

    def execute(self, request: ToolRequest) -> ToolResult:
        handler = self._tools.get(request.tool_name)
        if handler is None:
            return ToolResult(
                tool_name=request.tool_name,
                output_text="",
                success=False,
                reason="tool is not registered",
            )
        return ToolResult(
            tool_name=request.tool_name,
            output_text=handler(request.input_text),
            success=True,
            reason="tool executed",
        )

    @staticmethod
    def _echo(input_text: str) -> str:
        return input_text
