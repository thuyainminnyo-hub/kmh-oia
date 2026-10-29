# Local AI Production Pilot — Job Contract

Status: IMPLEMENTED ON PILOT BRANCH; AUTOMATED TESTS ADDED; EXECUTION NOT YET VERIFIED

## Scope
The initial contract defines a typed envelope for image/video production jobs. It is deliberately separate from the current KMH OIA runtime and does not invoke Ollama, ComfyUI, n8n, a GPU, or any external provider.

## Required controls
- Stable unique `job_id` per job.
- Explicit `asset_type` (`image` or `video`).
- Non-empty prompt and recognized lifecycle status.
- Non-negative attempt counter.
- ISO-8601 creation timestamp including timezone.
- Approved jobs must reference an output path.
- Validation fails closed for invalid fields.

## Current boundary
This contract does not yet implement queue persistence, retries, idempotency, model execution, output-file verification, human QA, cost measurement, or external business outcome verification. An output path is a reference, not proof that the file exists or is valid.

## Verification
Run from a checkout of this branch:

```bash
python -m unittest tests.test_production_job -v
python -m unittest discover -s tests -v
```

Test execution must be observed before marking this contract verified.
