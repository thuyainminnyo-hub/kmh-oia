# Local AI Production Pilot — ComfyUI Adapter

Status: IMPLEMENTED ON PILOT BRANCH; MOCKED HTTP TESTS ADDED; REAL SERVER NOT YET VERIFIED

## Implementation
`src/comfyui_adapter.py` provides a standard-library HTTP adapter for a locally running ComfyUI instance. It:
- Restricts the base URL to local HTTP hostnames.
- Loads a reviewed API-format workflow JSON from a configured local path.
- Replaces one explicitly configured prompt input.
- Submits the workflow to `POST /prompt`, polls `GET /history/{prompt_id}`, and downloads an image through `GET /view`.
- Writes output under a configured local root with a generated filename and bounded response size.
- Returns a normalized `AdapterResult` for the existing execution bridge.

Official reference: https://docs.comfy.org/development/comfyui-server/api-examples

## Test boundary
The unit tests mock HTTP responses and use synthetic bytes. They verify adapter behavior, not a real ComfyUI server or actual generated image.

## Local integration prerequisites
1. Install and run ComfyUI on the same machine as the KMH OIA process.
2. Export a workflow using ComfyUI's API format and ensure it contains a working image output node.
3. Configure the correct prompt node ID and input key from that workflow.
4. Call the adapter only after creating a job in `running` status.
5. Inspect the saved output file, then run the existing output verification and QA gates.

Example configuration (adjust the workflow path and node ID to the actual exported workflow):

```python
from src.comfyui_adapter import ComfyUIImageAdapter

adapter = ComfyUIImageAdapter(
    base_url="http://127.0.0.1:8188",
    workflow_path="config/comfyui-workflow-api.json",
    output_root="artifacts/local-ai",
    prompt_node_id="6",
    prompt_input_key="text",
)
```

Do not assume node ID `6` is correct for a user's workflow; it is only an example.

## Explicit limitations
- No real ComfyUI server, model, or GPU has been accessed by this change.
- Only image jobs are supported; video is rejected.
- The adapter does not provide durable queue persistence, retries, content safety review, semantic image QA, or cost accounting.
- Output bytes are not proof of visual quality or safety.
- Keep ComfyUI bound to localhost for this pilot; do not expose it to the public internet.
