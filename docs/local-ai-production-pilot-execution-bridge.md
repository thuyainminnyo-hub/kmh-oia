# Local AI Production Pilot — Execution Bridge

Status: IMPLEMENTED ON PILOT BRANCH; CI TEST WORKFLOW OBSERVED SUCCESS ON AN EARLIER COMMIT; CURRENT PATCH REQUIRES ITS OWN CHECKS

## Purpose
Connect the typed `ProductionJob` contract to an injected adapter without coupling KMH OIA to a particular local AI provider.

## Behavior
- Accepts only `queued` jobs.
- Sends an incremented-attempt job with `running` status to the adapter.
- Converts adapter exceptions and explicit failures to `failed`.
- Requires an explicit `allowed_output_root`.
- Rejects missing, empty, non-regular, or out-of-root output files before moving to `qa_pending`.
- Does not automatically approve an artifact; QA remains a separate gate.

## Current limitations
- The included tests use a fake adapter and synthetic files only.
- No Ollama, ComfyUI, n8n, GPU, queue persistence, retry scheduler, audit sink, or cost meter is connected.
- Filesystem verification does not establish image/video validity, content quality, or safety.
- The bridge is a synchronous in-process contract, not a production worker service.

## Verification
```bash
python -m unittest tests.test_production_execution -v
python -m unittest discover -s tests -v
```

Do not mark the current patch verified until its own CI checks finish.
