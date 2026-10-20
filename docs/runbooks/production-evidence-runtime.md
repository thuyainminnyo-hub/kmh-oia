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
