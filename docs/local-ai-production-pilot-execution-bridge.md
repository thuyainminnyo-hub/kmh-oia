# Local AI Production Pilot — Execution Bridge

Status: IMPLEMENTED ON PILOT BRANCH; TESTS ADDED; EXECUTION NOT YET VERIFIED

## Purpose
Connect the typed `ProductionJob` contract to an injected adapter without coupling KMH OIA to a particular local AI provider.

## Behavior
- Accepts only `queued` jobs.
- Sends an incremented-attempt job with `running` status to the adapter.
- Converts adapter exceptions and explicit failures to `failed`.
- Requires a non-empty output path on reported success.
- Requires the reported path to exist as a file before moving to `qa_pending`.
- Does not automatically approve an artifact; QA remains a separate gate.

## Current limitations
- The included tests use a fake adapter and synthetic files only.
- No Ollama, ComfyUI, n8n, GPU, queue persistence, retry scheduler, audit sink, or cost meter is connected.
- File existence does not establish image/video validity or content quality.
- The bridge is a synchronous in-process contract, not a production worker service.

## Verification
```bash
python -m unittest tests.test_production_execution -v
python -m unittest discover -s tests -v
```

Do not mark tests passing until execution output or CI evidence is available.
