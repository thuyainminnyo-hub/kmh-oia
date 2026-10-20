# Target-Host Replay Verification Runbook

Status: **PROPOSED PROCEDURE — NOT EXECUTED**
Scope: collect operator-verifiable evidence for the `target_host_persistent_storage_and_process_replay` gate. This runbook does not authorize deployment or change the release decision.

## Preconditions

- Use a disposable staging/test environment first. Do not run destructive tests against production data.
- Identify the exact commit intended for the test and compare it with the deployment evidence bundle's `bundle_commit_sha`. A mismatch is a **HOLD**.
- Ensure the operator is authorized to restart the service and inspect its storage.
- Never put API keys, access tokens, passwords, private keys, or customer data in the receipt or logs.
- Record timestamps in UTC. Redact public-facing hostnames if they are sensitive, but preserve a stable non-secret host/service identifier.

## Procedure

1. **Identify the target**
   - Record a stable `environment_id` and `host_or_service_id`.
   - Record the exact deployed Git commit SHA from the target itself (not from a local checkout alone).
   - Capture the UTC start time.

2. **Confirm persistence**
   - Record the application's configured database/state path.
   - Confirm that the path is backed by the intended persistent volume or durable storage service.
   - Record the evidence used to confirm the mount/volume (for example, a sanitized deployment configuration excerpt or operator check). A path string by itself is not proof of persistence.

3. **Write a test-only state marker**
   - Use a dedicated test session/key and non-sensitive marker value.
   - Execute the supported runtime path once and capture the returned trace or receipt.
   - Confirm the marker is persisted at the configured database/state path.
   - Do not use a real customer workflow or external side-effecting provider for this check.

4. **Restart the process**
   - Restart the target process using the environment's normal service manager.
   - Confirm the process is healthy and reports the same tested commit SHA.
   - Read the test marker back through the supported application interface. It must survive the restart.

5. **Test duplicate replay across independent processes**
   - Run the documented smoke test `sqlite_replay_across_independent_os_processes` against the same test database path using two independent OS processes.
   - The first process must be healthy and accept the test claim; the second must be healthy and reject the same claim with a reason identifying replay.
   - Record the observed database path and process outcomes. The second process must use the same persisted state, not an in-memory substitute.
   - If this mechanism is not implemented or the result cannot be observed, record the check as **NOT_VERIFIED**; do not fabricate a PASS receipt.
   - This local-file/process-boundary check does not prove cross-host atomicity.

6. **Produce the receipt**
   - Create the JSON receipt below from observed results.
   - Attach sanitized logs/config evidence as a JSON object or link to access-controlled evidence. Do not include secrets.
   - Have a second reviewer compare the receipt to the target and bundle before changing any gate status.

## Receipt template

Replace every placeholder and NOT_RUN value with observed values. The boolean values above are intentionally failing defaults; set them to true/false only when observed. Do not submit this template unchanged as evidence. The `smoke_test_report` field names and accepted values must match `scripts/deployment_evidence_bundle.py` exactly.

```json
{
  "environment_id": "<stable staging environment identifier>",
  "host_or_service_id": "<stable non-secret host/service identifier>",
  "commit_sha": "<full deployed commit SHA>",
  "database_path": "<observed configured state/database path>",
  "persistent_volume_confirmed": false,
  "smoke_tested_at_utc": "<RFC3339 UTC timestamp>",
  "smoke_test_report": {
    "schema_version": "1.0",
    "test": "sqlite_replay_across_independent_os_processes",
    "db_path": "<same observed database path as database_path>",
    "first_process": {
      "healthy": false,
      "accepted": false,
      "evidence_ref": "<sanitized evidence reference>"
    },
    "second_process": {
      "healthy": false,
      "accepted": false,
      "reason": "NOT_RUN",
      "evidence_ref": "<sanitized evidence reference>"
    },
    "result": "NOT_RUN",
    "test_marker_written": "NOT_RUN",
    "marker_survived_process_restart": "NOT_RUN",
    "post_restart_health_check": "NOT_RUN",
    "evidence_refs": []
  },
  "operator_notes": "No secrets or customer data."
}
```

## Acceptance criteria

The target-host gate may be considered for **PASS** only when all of the following are independently checked:

- All required fields are present and reflect observed values.
- The target's deployed full SHA exactly matches the evidence bundle's `bundle_commit_sha`.
- Persistent volume confirmation is `true` and supported by evidence.
- The test marker survives a process restart and the service is healthy afterward.
- The smoke-test report follows the exact validator schema: `schema_version`, `test`, `db_path`, `first_process`, `second_process`, and `result`.
- For a PASS, `test` is `sqlite_replay_across_independent_os_processes`; `first_process.healthy` and `first_process.accepted` are true; `second_process.healthy` is true, `second_process.accepted` is false, and `second_process.reason` identifies replay; `db_path` exactly matches `database_path`; `result` is `PASS`.
- The report includes a timestamp and inspectable supporting evidence.
- A reviewer confirms the evidence is from the claimed target environment.

Duplicate-replay protection must be reported separately and only passed if the implementation has a documented mechanism and the test demonstrates it. A single-host result does not satisfy the multi-host replay gate.

## Decision rules

- Missing evidence, SHA mismatch, uncertain persistence, or failed restart/read-back: **HOLD**.
- Confirmed harmful behavior: stop testing, preserve diagnostics, and follow the environment's incident/rollback procedure.
- Passing this gate alone does not establish provider authenticity, external business outcome, multi-host safety, or production readiness.
- No deployment, merge, or gate promotion is implied by completing this runbook.
