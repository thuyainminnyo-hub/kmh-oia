"""Read-only preflight for a local ComfyUI API workflow; never submits a job."""
from __future__ import annotations

import argparse
import ipaddress
import json
import math
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener


class _RejectRedirectHandler(HTTPRedirectHandler):
    """Reject redirects so preflight cannot leave the intended local endpoint."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def _normalize_local_base_url(base_url: object) -> tuple[str | None, str | None]:
    """Accept only plain HTTP URLs whose host is a literal loopback IP."""
    if not isinstance(base_url, str) or not base_url:
        return None, "base_url must be an HTTP URL using a literal loopback IP"

    try:
        parsed = urlparse(base_url)
        host = parsed.hostname
        port = parsed.port
        address = ipaddress.ip_address(host) if host else None
    except ValueError:
        return None, "base_url must contain a valid literal loopback IP and port"

    if parsed.scheme != "http" or address is None or not address.is_loopback:
        return None, "base_url must use HTTP and a literal loopback IP (127.0.0.1 or ::1)"
    if getattr(address, "scope_id", None) is not None:
        return None, "base_url must not use a scoped IPv6 address"
    if parsed.username is not None or parsed.password is not None:
        return None, "base_url must not include credentials"
    if parsed.query or parsed.fragment:
        return None, "base_url must not include a query or fragment"
    if parsed.path not in {"", "/"}:
        return None, "base_url must not include a path"
    if parsed.netloc.endswith(":") or (port is not None and not 1 <= port <= 65535):
        return None, "base_url port must be between 1 and 65535"

    return base_url.rstrip("/"), None


def validate_local_config(
    base_url: str,
    workflow_path: str | Path,
    prompt_node_id: str,
    prompt_input_key: str = "text",
    timeout_seconds: float = 3.0,
) -> list[str]:
    """Validate local workflow configuration and query ComfyUI's read-only API."""
    normalized_base_url, url_error = _normalize_local_base_url(base_url)
    if url_error:
        return [url_error]

    if (
        isinstance(timeout_seconds, bool)
        or not isinstance(timeout_seconds, (int, float))
        or not math.isfinite(timeout_seconds)
        or timeout_seconds <= 0
    ):
        return ["timeout_seconds must be a positive finite number"]

    try:
        workflow = json.loads(Path(workflow_path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"cannot read workflow JSON: {type(exc).__name__}: {exc}"]

    if not isinstance(workflow, dict) or not workflow:
        return ["workflow must be a non-empty JSON object"]

    node = workflow.get(prompt_node_id)
    if not isinstance(node, dict) or not isinstance(node.get("inputs"), dict):
        return [f"prompt node {prompt_node_id!r} or its inputs are missing"]
    if prompt_input_key not in node["inputs"]:
        return [f"prompt input key {prompt_input_key!r} is missing from node {prompt_node_id!r}"]

    request = Request(
        normalized_base_url + "/object_info",
        headers={"Accept": "application/json"},
        method="GET",
    )
    try:
        # Explicitly bypass environment/OS proxies and reject every redirect.
        opener = build_opener(ProxyHandler({}), _RejectRedirectHandler())
        with opener.open(request, timeout=timeout_seconds) as response:
            body = response.read(5_000_001)
        if len(body) > 5_000_000:
            return ["ComfyUI /object_info response exceeded 5 MB"]
        info = json.loads(body.decode("utf-8"))
        if not isinstance(info, dict):
            return ["ComfyUI /object_info response must be a JSON object"]
    except (HTTPError, URLError, TimeoutError, OSError, json.JSONDecodeError) as exc:
        return [f"cannot query local ComfyUI /object_info: {type(exc).__name__}: {exc}"]

    failures: list[str] = []
    for node_id, definition in workflow.items():
        if not isinstance(definition, dict):
            failures.append(f"workflow node {node_id!r} must be an object")
            continue
        class_type = definition.get("class_type")
        if not isinstance(class_type, str) or not class_type:
            failures.append(f"workflow node {node_id!r} has no class_type")
        elif class_type not in info:
            failures.append(f"workflow node {node_id!r} uses unregistered class {class_type!r}")
    return failures


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://127.0.0.1:8188")
    parser.add_argument("--workflow", required=True)
    parser.add_argument("--prompt-node-id", required=True)
    parser.add_argument("--prompt-input-key", default="text")
    parser.add_argument("--timeout-seconds", type=float, default=3.0)
    args = parser.parse_args()

    errors = validate_local_config(
        args.base_url,
        args.workflow,
        args.prompt_node_id,
        args.prompt_input_key,
        args.timeout_seconds,
    )
    if errors:
        for error in errors:
            print(f"FAIL: {error}")
        return 1

    print("PASS: local ComfyUI reachable; workflow JSON and node classes validated; no job submitted")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
