# Read-only Local ComfyUI Preflight

`scripts/comfyui_local_preflight.py` checks a local ComfyUI server and API-format workflow before generation. It calls only `GET /object_info`; it never submits a prompt.

From the repository root:

```bash
python scripts/comfyui_local_preflight.py --workflow /path/to/workflow_api.json --prompt-node-id 6 --prompt-input-key text
python -m unittest tests.test_comfyui_local_preflight -v
```

PASS means the local endpoint responded, the workflow JSON parsed, the configured prompt input exists, and every workflow node class appears in `/object_info`. It does not prove required model files exist, execution will succeed, or output quality is acceptable. The script refuses non-loopback URLs, uses a short timeout, caps response size, logs no credentials, and submits no job.
