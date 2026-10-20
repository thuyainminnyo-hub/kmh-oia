# Production Evidence Runtime — Configuration Runbook

Status: CONFIGURATION CONTRACT; NOT A LIVE DEPLOYMENT

## Purpose

Make the evidence-admission runtime's replay protection an explicit deployment decision. A successful startup and passing tests do not establish that an external provider is authentic, that a business outcome happened, or that the application is production-ready.

## Local single-host configuration

Create a persistent directory owned by the service account and provide a non-empty SQLite file path outside the repository, for example:

```python
from pathlib import Path

from src.live_operating_console import LiveOperatingConsole
from src.live_runtime_bridge import LiveRuntimeBridge
from src.receipt_replay_store import SQLiteReceiptReplayStore

database_path = Path("/var/lib/kmh-oia/evidence-replay.sqlite3")
database_path.parent.mkdir(parents=True, exist_ok=True)

replay_store = SQLiteReceiptReplayStore(str(database_path))
if not replay_store.health_check():
    raise RuntimeError("Evidence replay store health check failed")

bridge = LiveRuntimeBridge(
    console=LiveOperatingConsole(),
    receipt_replay_store=replay_store,
    require_durable_replay_store=True,
)
```

This is an integration pattern, not a drop-in application entry point: instantiate the console with the application's actual commands and inject a real provider-specific adapter plus its explicit allowlist before expecting trusted external evidence to be admitted.

## Deployment invariants

1. Set `require_durable_replay_store=True` for evidence-admitting runtime deployments.
2. Do not use `:memory:` for the SQLite path when durable replay protection is required.
3. Keep the database on persistent storage with service-account-only access and backup/restore policy.
4. SQLite replay protection is single-host/local-file scope. Multi-host runtimes require a shared transactional store that atomically enforces unique claims.
5. Register only a provider adapter whose verification mechanism is implemented and reviewed. A protocol or fake test adapter is not provider authentication.
6. Do not pass caller booleans as evidence of source authenticity or execution attribution.
7. Keep raw provider observations separate from human/model interpretation.
8. An internal QA PASS or runtime LEARNED state is not proof of external business success.
9. Keep `EXEC-SUN-TRAVEL-005` on HOLD until a real measurement channel, record, execution attribution, and verification receipt are connected and checked.

## Machine-Readable Readiness Snapshot

Run `python -m scripts.production_readiness_snapshot` to emit a JSON status snapshot. Exit code is 0 only when every gate is `PASS`; expected current behavior is exit code 2 with release decision `HOLD`, because live deployment, real-provider evidence, real business outcome and multi-host replay remain unverified. This report reflects repository-observable facts only; it does not query a live deployment.

## Deployment Evidence Bundle

Generate a conservative JSON handoff bundle from CI run metadata and optional operator-collected target-host evidence:

```bash
python -m scripts.deployment_evidence_bundle \
  --commit-sha "$GITHUB_SHA" \
  --ci-runs deployment-ci-runs.json \
  --target-evidence target-host-evidence.json \
  --output deployment-evidence-bundle.json
```

`--target-evidence` must be a JSON object containing all of these fields before the target-host gate can pass: `environment_id`, `host_or_service_id`, `persistent_volume_confirmed: true`, `database_path`, `smoke_test_report` with `result: "PASS"`, `smoke_tested_at_utc`, and `commit_sha` equal to the bundle SHA. Confirm mount persistence out-of-band before setting `persistent_volume_confirmed`; the bundle generator does not independently inspect the host or mount. CI runs only count as PASS when their head SHA matches the bundle SHA and their conclusion is `success`.

The validation workflow emits this bundle as the `kmh-oia-deployment-evidence-bundle` artifact. Its current CI-only bundle is expected to leave target host `NOT_VERIFIED`, provider authenticity `NOT_VERIFIED`, external business outcome `HOLD`, and multi-host replay `NOT_VERIFIED`. A JSON artifact is a handoff record, not a release approval.

## Deployment-host Replay Smoke Test

After the service owner has created the intended persistent SQLite database file on the target host, run:

```bash
python scripts/production_replay_smoke.py --db-path /var/lib/kmh-oia/evidence-replay.sqlite3
```

The command requires an existing file and will not silently create a new database on a possibly wrong path. It launches two separate Python processes, uses a fresh synthetic receipt identity, and expects the first claim to pass and the second to be rejected as replay. Capture the JSON output, the tested host/environment identifier, the commit SHA, and the UTC timestamp in the deployment evidence record. Do not include real provider secrets or sensitive receipt payloads.

A PASS proves only that the supplied SQLite file can be read and that a duplicate claim is rejected across local OS processes. It does not prove that the supplied path is truly on persistent mounted storage, that the full application is deployed correctly, that a real external provider is authentic, or that multi-host claims are safe. Independently confirm the volume/mount configuration and service-account permissions.

## Target-Host Evidence Capture Template

Copy `docs/runbooks/target-host-evidence.template.json` to a private deployment working directory and fill it from actual target-host observations; do not claim a persistent volume is confirmed unless the operator has independently checked the mount/volume configuration and service account permissions.

1. Confirm the intended SQLite database file exists on the persistent volume.
2. Run `python scripts/production_replay_smoke.py --db-path /var/lib/kmh-oia/evidence-replay.sqlite3` against that exact file.
3. Copy the complete JSON smoke report into `smoke_test_report`, record the UTC test time, environment and host/service identifier, set `persistent_volume_confirmed` to true only after checking the actual mount, and record the exact commit SHA tested.
4. Run `python -m scripts.deployment_evidence_bundle --commit-sha "$GITHUB_SHA" --ci-runs deployment-ci-runs.json --target-evidence target-host-evidence.json --output deployment-evidence-bundle.json`.
5. Review each gate independently. The bundle must still show provider authenticity as `NOT_VERIFIED`, external business outcome as `HOLD`, and multi-host replay as `NOT_VERIFIED` until separate evidence exists.

Never commit host identifiers, internal addresses, secrets, provider credentials, or real sensitive receipt payloads into a public repository. Keep the populated evidence JSON in the approved private release evidence store and share only redacted status/result summaries where appropriate.

## Capture target-host evidence receipt

Run this on the intended deployment host, from the exact git checkout you intend to validate. First confirm the database file is on the actual persistent mount, and initialize/health-check the replay database through the normal service configuration.

```bash
python -m scripts.capture_target_host_evidence \
  --db-path /var/lib/kmh-oia/evidence-replay.sqlite3 \
  --environment-id staging-or-production \
  --host-or-service-id host-or-service-identifier \
  --expected-commit-sha "$(git rev-parse HEAD)" \
  --confirm-persistent-volume \
  --output /secure/private-release-evidence/target-host-evidence.json
```

Only pass `--confirm-persistent-volume` after independently inspecting the mount/volume configuration on that host. The helper checks that the current checkout SHA exactly matches the supplied expected SHA, runs the independent-OS-process replay smoke test, and writes a gate-compatible receipt only when the smoke test passes. It records the UTC capture timestamp itself. It does not independently validate the platform mount configuration, authenticate an external provider, prove business success, or prove multi-host behavior.

If the target checkout lacks Git metadata, use a full clone or a release image/build process that can verify the immutable source SHA; do not fabricate or manually override the SHA.

## Evidence Status Matrix

The following matrix separates repository-level evidence from environment/provider evidence so a passing CI run cannot be mistaken for a production release.

| Gate | Evidence type | Current status | What closes the gate |
| --- | --- | --- | --- |
| Source compiles and repository preflight passes | Automated CI | Verified on last green commit | Re-run on exact release SHA |
| Runtime factory requires a durable replay store | Unit/integration tests + static preflight contract | Verified in repository | Preserve guard and rerun CI |
| Same receipt rejected after runtime recreation using retained SQLite file | Automated test with fake adapter | Verified in test fixture | Add real OS-process restart test in target environment |
| Persistent path and SQLite health in deployment | Environment/runtime evidence | Not yet externally verified | Deploy on persistent host path and capture startup/health results |
| Provider authenticity and execution attribution | External provider evidence | Not integrated | Implement and review provider-specific verification |
| Actual business outcome | External source/measurement receipt | Not verified | Capture source record with execution attribution and independent verification |
| Multi-host duplicate protection | Shared transactional backend | Not implemented | Deploy shared store with atomic unique claims and concurrency test |

Never mark the external-provider, live-deployment, business-outcome, or multi-host rows complete based only on unit tests, fake adapters, static checks, or repository-level CI.

## Release checklist

- [ ] Persistent store path is explicit and writable by the service account.
- [ ] Store health check passes during startup.
- [ ] Configuration rejects both `:memory:` and all `file:` SQLite URI paths; the runtime factory accepts ordinary file paths only.
- [ ] Repository deployment preflight verifies that the production runtime factory and this runbook exist, and that core safety-contract markers remain present.
- [ ] Automated replay regression builds two fresh runtime instances against the same retained SQLite file and rejects the repeated receipt.
- [ ] A real OS-process restart test proves replay claims survive process termination and recreation in the target deployment environment.
- [ ] Duplicate receipt test is rejected across independent connections to the same store.
- [ ] Provider-specific verification uses the provider's actual supported authenticity mechanism.
- [ ] Provider record is explicitly and verifiably attributed to the KMH OIA execution.
- [ ] Timeout, unreachable provider, invalid receipt, stale receipt, replay and unknown provider fail closed.
- [ ] GitHub Actions unit tests and repository validation pass on the exact release commit.
- [ ] Real external outcome evidence is reviewed separately from internal QA.

## Current boundary

The repository provides generic trusted-receipt contracts, fake-adapter tests, and a durable local SQLite replay store. This runbook documents how to wire those components; it does not create a deployment, provision secrets, connect a real provider, supply a distributed database, or verify any external business outcome.
