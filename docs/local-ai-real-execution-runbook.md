# Local ComfyUI Real-Execution Verification Runbook

Status: RUNBOOK ONLY — NOT EVIDENCE THAT A LIVE RUN HAS OCCURRED

## Goal

Execute one explicitly approved, low-cost local image workflow through the KMH OIA ComfyUI adapter, then retain enough evidence to independently verify the run. Use only synthetic/non-sensitive prompts and assets.

## Preconditions

- ComfyUI is installed and running locally.
- The selected workflow is exported in API format and uses nodes/models installed in this ComfyUI instance.
- The configured base URL points to the intended local instance (prefer loopback, e.g. `http://127.0.0.1:8188`).
- No public ingress, cloud deployment, paid partner API node, or production credential is required for this pilot.
- The operator has reviewed the workflow and understands its compute/time cost.
- Use a fresh temporary output directory and a synthetic prompt.

## Execution procedure

1. Record the git commit SHA and Python/ComfyUI versions.
2. Confirm the local health endpoint responds; record timestamp and status without logging secrets.
3. Validate that the API workflow JSON is loadable and all required node classes/models exist.
4. Submit exactly one job through the KMH OIA adapter.
5. Record the actual provider `prompt_id` returned by ComfyUI. Do not invent or substitute an ID.
6. Wait for a terminal execution state. Distinguish completed, failed, timed out, and cancelled.
7. Retrieve the output using the metadata returned by ComfyUI; ensure it resolves under the configured allowed output root.
8. Verify non-empty file, expected image signature, successful image decoding, and reasonable dimensions. Signature-only checks are not full decoding.
9. Compute SHA-256 over the exact output bytes.
10. Record an audit event linking job ID, actual prompt ID, workflow/model identifiers, output relative path, SHA-256, timestamps, elapsed time, and result status. Never record tokens or secrets.
11. Keep job status at `qa_pending`. A human or separately validated QA process must record approve/reject with actor, timestamp, criteria/version, and rationale.
12. Attach logs/results to the PR or verification record, redacting local usernames, absolute paths, tokens, and other sensitive data.

## Evidence checklist

- [ ] Exact source commit SHA
- [ ] ComfyUI version and workflow file SHA-256
- [ ] Actual provider prompt ID
- [ ] Terminal execution status and elapsed time
- [ ] Output relative path, byte size, dimensions, format/decode result
- [ ] Output SHA-256
- [ ] Audit event and audit-chain verification result
- [ ] QA decision, reviewer/actor, criteria version, and rationale
- [ ] Failure/cleanup notes, if any

## Stop conditions

Stop and mark the run NOT PASSED if the provider ID is missing, execution status is ambiguous, output is missing/outside the allowed root, format/decode verification fails, audit persistence fails, or evidence fields disagree. Do not auto-approve.

## What this runbook does not prove

This document does not run ComfyUI, establish that a local server is available, prove that a model was loaded, or certify visual quality, safety, cost savings, or production readiness. Those claims require captured evidence from an actual run.
