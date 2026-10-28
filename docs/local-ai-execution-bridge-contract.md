# Local AI Production Pilot — Execution Bridge Contract

## Purpose

Normalize the boundary between a production job and an execution provider. The
contract is intentionally provider-neutral so a future Ollama or ComfyUI adapter
can be added without treating provider-specific responses as verified outputs.

## Current implementation

- `ProductionAdapter` defines the adapter interface.
- `ExecutionResult` validates normalized success/failure results.
- `FakeProductionAdapter` deterministically returns a virtual `fake://` output
  reference or a configured failure.
- `tests/test_production_adapter.py` covers result validation and fake execution.

## Explicit limits

The fake adapter does **not** invoke Ollama, ComfyUI, n8n, a GPU, or any external
service. It does not create an output file, persist a job, perform retries,
prove that a file exists, run QA, or measure costs. A `fake://` reference is a
test placeholder, not a deliverable. A successful adapter result is not by
itself evidence that an asset is safe or acceptable.

## Next verification gates

1. Run the full unit-test suite and record the actual exit status.
2. Add a local adapter behind explicit configuration and a bounded timeout.
3. Verify the returned file exists and matches an expected output directory.
4. Run a separate QA gate; do not equate execution success with approval.
5. Record request ID, job ID, adapter name, result, elapsed time, output digest,
   QA decision, and estimated resource cost in an audit event.
6. Run a controlled synthetic job before enabling real production workloads.
