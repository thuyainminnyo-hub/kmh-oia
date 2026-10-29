"""Bounded local ComfyUI image-generation adapter for the pilot.

Uses only the Python standard library. Integration requires a reviewed
ComfyUI API-format workflow JSON and a running local ComfyUI server.
"""
from __future__ import annotations

import ipaddress
import json
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlparse
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener
from uuid import uuid4

from src.production_execution import AdapterResult
from src.production_job import ProductionJob


class ComfyUIAdapterError(RuntimeError):
    """Raised for invalid configuration or a failed ComfyUI interaction."""


class _RejectRedirectHandler(HTTPRedirectHandler):
    """Fail closed: local API responses must never redirect to another host."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class ComfyUIImageAdapter:
    """Execute image jobs through a local ComfyUI HTTP API."""

    name = "comfyui-local"

    def __init__(
        self,
        *,
        base_url: str,
        workflow_path: str | Path,
        output_root: str | Path,
        prompt_node_id: str,
        prompt_input_key: str = "text",
        request_timeout_seconds: float = 10.0,
        job_timeout_seconds: float = 300.0,
        poll_interval_seconds: float = 0.5,
        max_output_bytes: int = 25_000_000,
    ) -> None:
        if not isinstance(base_url, str):
            raise ValueError("base_url must be a local HTTP URL using a literal loopback IP")
        try:
            parsed = urlparse(base_url)
            host = parsed.hostname
            port = parsed.port
            address = ipaddress.ip_address(host) if host else None
        except ValueError as exc:
            raise ValueError("base_url must contain a valid literal loopback IP and port") from exc
        if parsed.scheme != "http" or address is None or not address.is_loopback:
            raise ValueError("base_url must use HTTP and a literal loopback IP (127.0.0.1 or ::1)")
        if parsed.username or parsed.password or parsed.query or parsed.fragment:
            raise ValueError("base_url must not include credentials, query, or fragment")
        if parsed.path not in {"", "/"}:
            raise ValueError("base_url must not include a path")
        if port is not None and not 1 <= port <= 65535:
            raise ValueError("base_url port must be between 1 and 65535")
        if not isinstance(prompt_node_id, str) or not prompt_node_id.strip():
            raise ValueError("prompt_node_id must be a non-empty string")
        if not isinstance(prompt_input_key, str) or not prompt_input_key.strip():
            raise ValueError("prompt_input_key must be a non-empty string")
        if request_timeout_seconds <= 0 or job_timeout_seconds <= 0 or poll_interval_seconds <= 0:
            raise ValueError("timeouts and poll interval must be positive")
        if isinstance(max_output_bytes, bool) or not isinstance(max_output_bytes, int) or max_output_bytes <= 0:
            raise ValueError("max_output_bytes must be a positive integer")

        self.base_url = base_url.rstrip("/")
        self.workflow_path = Path(workflow_path)
        self.output_root = Path(output_root).resolve()
        self.prompt_node_id = prompt_node_id
        self.prompt_input_key = prompt_input_key
        self.request_timeout_seconds = request_timeout_seconds
        self.job_timeout_seconds = job_timeout_seconds
        self.poll_interval_seconds = poll_interval_seconds
        self.max_output_bytes = max_output_bytes

    def execute(self, job: ProductionJob) -> AdapterResult:
        if not isinstance(job, ProductionJob):
            raise TypeError("job must be a ProductionJob")
        if job.asset_type != "image":
            return AdapterResult(False, error_message="ComfyUI image adapter only supports image jobs")
        if job.status != "running":
            return AdapterResult(False, error_message="job must be in running status")
        try:
            workflow = json.loads(self.workflow_path.read_text(encoding="utf-8"))
            if not isinstance(workflow, dict):
                raise ComfyUIAdapterError("workflow must be a JSON object")
            node = workflow.get(self.prompt_node_id)
            if not isinstance(node, dict) or not isinstance(node.get("inputs"), dict):
                raise ComfyUIAdapterError("configured prompt node/input was not found in workflow")
            if self.prompt_input_key not in node["inputs"]:
                raise ComfyUIAdapterError("configured prompt input key was not found in workflow")
            node["inputs"][self.prompt_input_key] = job.prompt
            submitted = self._request_json(
                "POST",
                "/prompt",
                {"prompt": workflow, "client_id": str(uuid4())},
            )
            prompt_id = submitted.get("prompt_id")
            if not isinstance(prompt_id, str) or not prompt_id:
                raise ComfyUIAdapterError("ComfyUI did not return a prompt_id")
            deadline = time.monotonic() + self.job_timeout_seconds
            history_entry = None
            while time.monotonic() < deadline:
                history = self._request_json("GET", f"/history/{prompt_id}")
                candidate = history.get(prompt_id) if isinstance(history, dict) else None
                if isinstance(candidate, dict):
                    status = candidate.get("status", {})
                    status_text = status.get("status_str", "") if isinstance(status, dict) else ""
                    if status_text.lower() in {"error", "failed"}:
                        raise ComfyUIAdapterError("ComfyUI reported execution failure")
                    # Do not treat partial output metadata as completion. Wait for
                    # an explicit successful terminal status before downloading.
                    if status_text.lower() == "success":
                        if not isinstance(candidate.get("outputs"), dict):
                            raise ComfyUIAdapterError("successful history entry has no outputs object")
                        history_entry = candidate
                        break
                time.sleep(min(self.poll_interval_seconds, max(0.0, deadline - time.monotonic())))
            if history_entry is None:
                raise ComfyUIAdapterError("timed out waiting for ComfyUI output")
            image_meta = self._first_image(history_entry.get("outputs", {}))
            filename = image_meta["filename"]
            subfolder = image_meta.get("subfolder", "")
            image_type = image_meta.get("type", "output")
            self._validate_image_metadata(filename, subfolder, image_type)
            suffix = Path(filename).suffix.lower()
            if suffix not in {".png", ".jpg", ".jpeg", ".webp"}:
                raise ComfyUIAdapterError("unsupported output image extension")
            raw = self._request_bytes(
                "/view?" + urlencode({
                    "filename": filename,
                    "subfolder": subfolder,
                    "type": image_type,
                })
            )
            if not raw:
                raise ComfyUIAdapterError("ComfyUI returned an empty image")
            if len(raw) > self.max_output_bytes:
                raise ComfyUIAdapterError("ComfyUI image exceeded max_output_bytes")
            if not self._matches_image_signature(suffix, raw):
                raise ComfyUIAdapterError("image bytes do not match the declared file extension")
            self.output_root.mkdir(parents=True, exist_ok=True)
            destination = (self.output_root / f"{job.job_id}-{uuid4().hex}{suffix}").resolve()
            destination.relative_to(self.output_root)
            destination.write_bytes(raw)
            if destination.stat().st_size <= 0:
                destination.unlink(missing_ok=True)
                raise ComfyUIAdapterError("saved output image is empty")
            return AdapterResult(True, output_path=str(destination), provider_execution_id=prompt_id)
        except (OSError, json.JSONDecodeError, HTTPError, URLError, TimeoutError, KeyError, TypeError, ValueError, ComfyUIAdapterError) as exc:
            return AdapterResult(False, error_message=f"{type(exc).__name__}: {exc}")

    @staticmethod
    def _validate_image_metadata(filename: object, subfolder: object, image_type: object) -> None:
        """Reject path/query abuse in server-returned image metadata before /view requests."""
        if not isinstance(filename, str) or not filename or filename in {".", ".."}:
            raise ComfyUIAdapterError("invalid output image filename")
        if "/" in filename or "\\" in filename or any(ord(char) < 32 or ord(char) == 127 for char in filename):
            raise ComfyUIAdapterError("output image filename must be a single safe path component")
        if not isinstance(subfolder, str):
            raise ComfyUIAdapterError("invalid output image subfolder")
        if subfolder:
            if subfolder.startswith(("/", "\\")) or "\\" in subfolder:
                raise ComfyUIAdapterError("output image subfolder must be a safe relative path")
            parts = subfolder.split("/")
            if any(part in {"", ".", ".."} for part in parts):
                raise ComfyUIAdapterError("output image subfolder contains an unsafe path segment")
            if any(any(ord(char) < 32 or ord(char) == 127 for char in part) or ":" in part for part in parts):
                raise ComfyUIAdapterError("output image subfolder contains an invalid path character")
        if image_type not in {"input", "output", "temp"}:
            raise ComfyUIAdapterError("unsupported ComfyUI image type")

    @staticmethod
    def _matches_image_signature(suffix: str, raw: bytes) -> bool:
        """Check a minimal container signature; this is not full image decoding."""
        if suffix == ".png":
            return raw.startswith(b"\x89PNG\r\n\x1a\n")
        if suffix in {".jpg", ".jpeg"}:
            return raw.startswith(b"\xff\xd8\xff")
        if suffix == ".webp":
            return len(raw) >= 12 and raw.startswith(b"RIFF") and raw[8:12] == b"WEBP"
        return False

    @staticmethod
    def _first_image(outputs: dict) -> dict:
        for node_output in outputs.values():
            if not isinstance(node_output, dict):
                continue
            images = node_output.get("images")
            if isinstance(images, list):
                for item in images:
                    if isinstance(item, dict) and isinstance(item.get("filename"), str) and item["filename"]:
                        return item
        raise ComfyUIAdapterError("ComfyUI history contained no output image metadata")

    def _request_json(self, method: str, path: str, payload: dict | None = None) -> dict:
        body = None if payload is None else json.dumps(payload).encode("utf-8")
        headers = {"Accept": "application/json"}
        if body is not None:
            headers["Content-Type"] = "application/json"
        request = Request(self.base_url + path, data=body, headers=headers, method=method)
        with build_opener(ProxyHandler({}), _RejectRedirectHandler()).open(request, timeout=self.request_timeout_seconds) as response:
            data = response.read(2_000_001)
        if len(data) > 2_000_000:
            raise ComfyUIAdapterError("ComfyUI JSON response exceeded 2 MB limit")
        decoded = json.loads(data.decode("utf-8"))
        if not isinstance(decoded, dict):
            raise ComfyUIAdapterError("ComfyUI returned an unexpected JSON shape")
        return decoded

    def _request_bytes(self, path: str) -> bytes:
        request = Request(self.base_url + path, headers={"Accept": "image/*"}, method="GET")
        with build_opener(_RejectRedirectHandler()).open(request, timeout=self.request_timeout_seconds) as response:
            data = response.read(self.max_output_bytes + 1)
        if len(data) > self.max_output_bytes:
            raise ComfyUIAdapterError("ComfyUI image exceeded max_output_bytes")
        return data
