"""Read-only preflight for a local ComfyUI API workflow; never submits a job."""
from __future__ import annotations
import argparse, json
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

def validate_local_config(base_url: str, workflow_path: str | Path, prompt_node_id: str,
                          prompt_input_key: str = "text", timeout_seconds: float = 3.0) -> list[str]:
    parsed = urlparse(base_url)
    if parsed.scheme != "http" or parsed.hostname not in {"localhost", "127.0.0.1", "::1"}:
        return ["base_url must be local HTTP (localhost, 127.0.0.1, or ::1)"]
    if parsed.username or parsed.password or parsed.query or parsed.fragment:
        return ["base_url must not include credentials, query, or fragment"]
    if timeout_seconds <= 0:
        return ["timeout_seconds must be positive"]
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
    request = Request(base_url.rstrip("/") + "/object_info", headers={"Accept": "application/json"})
    try:
        with urlopen(request, timeout=timeout_seconds) as response:
            body = response.read(5_000_001)
        if len(body) > 5_000_000:
            return ["ComfyUI /object_info response exceeded 5 MB"]
        info = json.loads(body.decode("utf-8"))
        if not isinstance(info, dict):
            return ["ComfyUI /object_info response must be a JSON object"]
    except (HTTPError, URLError, TimeoutError, OSError, json.JSONDecodeError) as exc:
        return [f"cannot query local ComfyUI /object_info: {type(exc).__name__}: {exc}"]
    failures=[]
    for node_id, definition in workflow.items():
        if not isinstance(definition, dict):
            failures.append(f"workflow node {node_id!r} must be an object"); continue
        class_type=definition.get("class_type")
        if not isinstance(class_type, str) or not class_type:
            failures.append(f"workflow node {node_id!r} has no class_type")
        elif class_type not in info:
            failures.append(f"workflow node {node_id!r} uses unregistered class {class_type!r}")
    return failures

def main() -> int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://127.0.0.1:8188")
    parser.add_argument("--workflow", required=True)
    parser.add_argument("--prompt-node-id", required=True)
    parser.add_argument("--prompt-input-key", default="text")
    parser.add_argument("--timeout-seconds", type=float, default=3.0)
    args=parser.parse_args()
    errors=validate_local_config(args.base_url,args.workflow,args.prompt_node_id,args.prompt_input_key,args.timeout_seconds)
    if errors:
        for error in errors: print(f"FAIL: {error}")
        return 1
    print("PASS: local ComfyUI reachable; workflow JSON and node classes validated; no job submitted")
    return 0
if __name__ == "__main__":
    raise SystemExit(main())
