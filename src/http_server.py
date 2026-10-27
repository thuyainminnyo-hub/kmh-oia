"""Minimal HTTP adapter for running KMH OIA on Cloud Run.

This adapter exposes liveness and a bounded JSON execution endpoint. It does
not claim dependency readiness, authenticate an external provider, or authorize
production use. Put authenticated ingress in front of /run before deployment.
"""
from __future__ import annotations

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from typing import Any

from src.main import run

MAX_BODY_BYTES = 64 * 1024
MAX_GOAL_BYTES = 8 * 1024
MAX_SESSION_ID_CHARS = 128


class OIARequestHandler(BaseHTTPRequestHandler):
    server_version = "KMH-OIA-HTTP/0.1"

    def _send_json(self, status: int, payload: dict[str, Any]) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        if self.path == "/healthz":
            self._send_json(200, {"status": "ok", "check": "liveness"})
            return
        self._send_json(404, {"error": "not_found"})

    def do_POST(self) -> None:
        if self.path != "/run":
            self._send_json(404, {"error": "not_found"})
            return
        raw_length = self.headers.get("Content-Length")
        try:
            length = int(raw_length or "")
        except ValueError:
            self._send_json(411, {"error": "content_length_required"})
            return
        if length < 0:
            self._send_json(400, {"error": "invalid_content_length"})
            return
        if length > MAX_BODY_BYTES:
            self._send_json(413, {"error": "request_too_large"})
            return
        if self.headers.get("Transfer-Encoding"):
            self._send_json(400, {"error": "transfer_encoding_not_supported"})
            return
        if self.headers.get_content_type() != "application/json":
            self._send_json(415, {"error": "application_json_required"})
            return
        try:
            payload = json.loads(self.rfile.read(length))
        except (json.JSONDecodeError, UnicodeDecodeError):
            self._send_json(400, {"error": "invalid_json"})
            return
        if not isinstance(payload, dict):
            self._send_json(400, {"error": "json_object_required"})
            return
        goal = payload.get("goal")
        session_id = payload.get("session_id", "default")
        if not isinstance(goal, str) or not goal.strip():
            self._send_json(400, {"error": "goal_must_be_non_empty_string"})
            return
        if len(goal.encode("utf-8")) > MAX_GOAL_BYTES:
            self._send_json(413, {"error": "goal_too_long"})
            return
        if not isinstance(session_id, str) or not session_id.strip():
            self._send_json(400, {"error": "session_id_must_be_non_empty_string"})
            return
        if len(session_id) > MAX_SESSION_ID_CHARS:
            self._send_json(400, {"error": "session_id_too_long"})
            return
        try:
            response, trace = run(goal, session_id=session_id)
        except (ValueError, PermissionError):
            self._send_json(400, {"error": "execution_rejected"})
            return
        except Exception:
            # Do not expose exception messages or internal details to clients.
            self._send_json(500, {"error": "internal_error"})
            return
        self._send_json(200, {
            "response": response,
            "stages": trace.stages,
            "events": [
                {"stage": event.stage, "status": event.status, "metadata": event.metadata}
                for event in trace.events
            ],
        })

    def log_message(self, format: str, *args: object) -> None:
        # Keep request bodies and arbitrary user content out of default access logs.
        return


def main() -> None:
    port = int(os.environ.get("PORT", "8080"))
    if not 1 <= port <= 65535:
        raise ValueError("PORT must be between 1 and 65535")
    server = ThreadingHTTPServer(("0.0.0.0", port), OIARequestHandler)
    try:
        server.serve_forever()
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
