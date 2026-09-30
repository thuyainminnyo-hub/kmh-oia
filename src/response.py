"""Response boundary for validated KMH OIA results."""

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class Response:
    text: str


class Responder(Protocol):
    """Boundary that turns an accepted result into a user-facing response."""

    def render(self, text: str) -> Response: ...


class DeterministicResponder:
    """Return accepted text without adding model-specific behavior."""

    def render(self, text: str) -> Response:
        return Response(text=text)
