# Local AI Provider Decision — Pilot v1

Decision status: PROPOSED FOR REVIEW; NO PROVIDER CONNECTED YET

## Decision

Use **ComfyUI as the first image-generation adapter target** for the Local AI Production Intelligence Pilot. Keep the provider behind the existing `ProductionAdapter` / `ProductionExecutionBridge` boundary. Treat Ollama as a possible later text-model service for prompt assistance or metadata, not as the image renderer for this first slice.

## Official API evidence

- ComfyUI API examples: https://docs.comfy.org/development/comfyui-server/api-examples
  - The official examples require exporting a workflow in API format.
  - The server accepts a workflow through `POST /prompt`.
  - A reliable result flow monitors execution, reads `/history/{prompt_id}`, then retrieves generated images through `/view`.
- ComfyUI server routes: https://docs.comfy.org/development/comfyui-server/comms_routes
  - The `/prompt` route validates and queues a workflow, returning a prompt ID or validation errors.
- Ollama generate API: https://docs.ollama.com/api/generate
  - Ollama exposes `POST /api/generate` for text generation and documents timing/token metrics. This is useful for text tasks, but does not itself replace an image-generation workflow.

## Proposed adapter contract

1. Load a reviewed ComfyUI API-format workflow template from a configured local file.
2. Validate the configured prompt node ID and input field before modifying the workflow.
3. Submit to a configured local ComfyUI base URL with a bounded request timeout.
4. Record the returned prompt ID and poll history or completion state until success/failure/timeout.
5. Retrieve only supported output images from the returned history.
6. Save outputs beneath a configured output root using safe, generated filenames.
7. Pass each saved file through `verify_output_file` and the execution bridge's allowed-root check.
8. Move successful outputs only to `qa_pending`; a separate QA decision is required before approval.

## Safety and scope boundaries

- No remote provider, cloud API, or external website is called by this proposed local adapter.
- Do not expose ComfyUI's local server to the public internet for this pilot.
- Do not accept arbitrary workflow JSON from untrusted requests; use a reviewed template and a fixed allowlisted prompt input.
- Use request and total-job timeouts; handle malformed JSON, HTTP errors, validation errors, empty history, missing output images, and output-size limits.
- Never claim real generation until an actual local ComfyUI instance, compatible workflow, model, and output file have been tested.
- No real ComfyUI adapter is implemented by this decision document. Current adapter tests remain fake/synthetic.

## Acceptance criteria for implementation

- Unit tests mock HTTP interactions and cover queue success, queue rejection, timeout, failed history, missing image metadata, file-download failure, path containment, and empty output.
- Integration test is opt-in and requires an explicitly configured local ComfyUI server and API workflow fixture.
- Evidence includes prompt ID, adapter version, elapsed time, output path/digest, verification result, and QA decision.
- No CI test is described as a real model-generation test unless it actually connects to a model server.
