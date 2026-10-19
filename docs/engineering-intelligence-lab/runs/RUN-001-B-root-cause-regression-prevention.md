# RUN 001-B — Root Cause Analysis & Regression Prevention

**Project:** KMH Engineering Intelligence Lab  
**Parent:** KMH AI Production Studio  
**Operating loop:** Build → Connect → Run → Verify  
**Run type:** Non-production tabletop / evidence-planning exercise  
**Device constraint:** Android phone only; no CLI, cluster, cloud deployment, or paid resource assumed.

## Objective
Turn the RUN 001-A incident signal into testable hypotheses and a regression-prevention plan without prematurely declaring a root cause.

## Known scenario evidence (fictional training data)
- Before rollback: HTTP 5xx 4.8%; p95 latency 1.4 s; frequent dependency timeouts; CPU 55%.
- After rollback: HTTP 5xx 0.3%; p95 latency 280 ms; dependency timeouts significantly reduced; CPU 53%.
- Interpretation: improvement after rollback supports a release-related regression hypothesis, but does not prove the exact cause. These values are not live telemetry.

## Competing hypotheses
1. **H1 — Downstream-call regression:** the new release changed a dependency call path, timeout, retry, or connection handling.
2. **H2 — Configuration drift:** an environment/configuration change coincided with the release.
3. **H3 — Dependency-side event:** a downstream service degraded independently and the timing overlapped with the release.
4. **H4 — Traffic/data interaction:** a request mix or payload pattern exposed a defect not visible under normal test traffic.

## Evidence required before confirming a cause
- Exact deployment and configuration change timeline.
- Version-to-version diff and relevant feature flags.
- Correlated request IDs across application logs and traces, with secrets/PII redacted.
- Dependency latency, timeout, retry, and error metrics over the same time window.
- Traffic volume and request mix before/during/after the incident.
- Reproduction in a safe staging/test environment, if available.

## Regression test plan
- **T1 — Dependency timeout:** simulate a slow downstream response; verify bounded timeout behavior and controlled error handling.
- **T2 — Retry budget:** verify retries are bounded, do not amplify load, and respect idempotency.
- **T3 — Error propagation:** verify dependency failures produce expected API status codes and useful, non-sensitive logs.
- **T4 — Latency/error guard:** use a defined test window and thresholds for p95 latency and 5xx rate; stop the rollout if guardrails are breached.
- **T5 — Rollback compatibility:** verify the previous version can safely read/write shared data and work with current configuration.
- **T6 — Observability:** ensure request IDs, dependency timings, and failure reasons can be correlated without logging credentials or sensitive payloads.

## Decision rules
- Do not select a single root cause from correlation alone.
- Prefer the hypothesis that survives reproduction and is supported by multiple independent evidence sources.
- If evidence conflicts or reproduction fails, keep the cause **UNCONFIRMED** and gather more data.
- Add the smallest regression test that would have failed before the fix and passes after it.
- Any real rollback or production change must follow the service owner's approved incident policy.

## Run checklist
- [ ] Select the leading hypothesis and at least one alternative.
- [ ] Name the evidence that would confirm and falsify each.
- [ ] Choose a minimal regression test and expected result.
- [ ] Record actual result and evidence link only after a real test.
- [ ] Review prevention action and owner before closing follow-up work.

## Status
- Build: RUN CARD CREATED.
- Connect: GitHub record and Notion log intended to cross-reference each other; automatic sync is **UNTESTED**.
- Run: **PENDING** — this plan has not been executed against a real service.
- Verify: **PENDING** — no reproduction artifacts or live telemetry supplied.
- Production PASS: **NOT CLAIMED**.

## Next action
Run a tabletop hypothesis-selection checkpoint. Then, if a safe test environment and evidence are available, execute only the selected regression test there. Otherwise keep the run marked PENDING/BLOCKED rather than inventing results.
