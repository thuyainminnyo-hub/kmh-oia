# TGiTrailRun Runner Safety Pilot — Security Review Note

**Status:** HOLD / NOT VERIFIED  
**Scope:** Code review of the synthetic-data pilot on `pilot/tgi-trailrun-runner-safety`. This note is not event-owner approval or a production security certification.

## Verified evidence

- Earlier candidate commit `c326137f4173fa615a480aaee1121913d5253d02` passed Tests and Validation:
  - Tests: https://github.com/thuyainminnyo-hub/kmh-oia/actions/runs/40623684589
  - Validation: https://github.com/thuyainminnyo-hub/kmh-oia/actions/runs/40623684350
- The current candidate adds store-boundary transition authorization, service-boundary JSON Schema validation, and checkpoint-scope checks for create/read/audit/transition paths, with negative tests.
- CI must be checked against the latest branch head before considering this candidate verified.

## Security gaps that remain open

1. **Authentication is not implemented here.** The `role` argument is caller-supplied. A real API must derive the role from a verified identity/session/token and must not trust a request-body role.
2. **Caller-supplied role is still not trusted identity.** The store now checks the role/action policy for transitions as defense in depth, but `actor_role` remains a string supplied by the caller. A real API must derive role from a verified identity and must not trust request-body roles.
3. **Checkpoint scope requires a trusted adapter.** The service now restricts create/read/audit/transition to `allowed_checkpoint_ids`; omitted scope defaults to deny. The module itself does not authenticate callers or derive this set. Do not expose it to a network endpoint until a verified identity adapter supplies scope and runner-level scope requirements are reviewed.
4. **Role matrix is provisional.** Race director and medical lead must approve role-to-action mapping, especially who may acknowledge, dispatch, resolve, and close incidents.
5. **Schema validation is enforced at the service create boundary, but not every direct store call.** Network-facing integrations must only expose the service boundary, and the storage layer should eventually be made private or independently validate complete payloads.
6. **Persistence is local SQLite only.** No evidence yet for multi-host deployment, production backup/restore, disaster recovery, or multi-replica concurrency.
7. **No live dispatch/notifications or emergency service integration exists.** Do not describe this pilot as a rescue dispatch system.

## Required security acceptance tests

- Unauthenticated request is denied.
- Request-body role spoofing is denied.
- Volunteer cannot dispatch through any public or internal write path.
- A caller cannot create, read, transition, or read audit for an incident outside their supplied checkpoint scope.
- Unauthorized attempts leave status, receipt, and audit records unchanged.
- Invalid schema payloads are rejected by the service before persistence.
- Direct store transition calls cannot use a disallowed role/action transition.
- Audit log contains a trusted actor identifier, not just a free-form role.
- CI is green for the exact candidate commit.
- Race director, medical lead, privacy owner, and security reviewer sign off before any real data or field trial.

## Release decision

**HOLD / NOT VERIFIED.** Do not merge as production-ready, deploy, or use real runner/medical data until the open gaps and Gate C/D requirements in `runner-safety-pilot.md` have evidence and explicit owner approval.

## Exact-head CI evidence captured before this documentation-only refresh — 2026-10-28

The last CI-verified candidate before this documentation-only refresh was `26c60dd26ac4deba5354f779f832e9ab32f7481e`. It was the PR branch head at the time of the runs; later documentation commits must be checked against their own exact SHA before claiming current-head verification.

- [KMH OIA Tests #40725848141 — success](https://github.com/thuyainminnyo-hub/kmh-oia/actions/runs/40725848141). The exact-candidate test log records **517 tests, OK** (`Ran 517 tests in 0.957s`), including the three synthetic SQLite failure-injection tests:
  - `test_failed_receipt_insert_rolls_back_create_and_allows_clean_retry`
  - `test_failed_initial_audit_insert_rolls_back_incident_and_receipt`
  - `test_failed_transition_audit_insert_rolls_back_state_change`
- [KMH OIA Validation #40725848144 — success](https://github.com/thuyainminnyo-hub/kmh-oia/actions/runs/40725848144). Tests, repository-validation, performance-evidence, and deployment-evidence-bundle jobs completed successfully.

An earlier local Colab verification was reported for commit `4cc4499144d951ae0cf9f5b492d3b1d508db58e0` (Python 3.12.3, 514 tests, compile/preflight/diff checks passed). That run is not an exact-head local run for `26c60dd...`; no local checkout execution for that candidate or any later commit is evidenced here.

The formal reviewer submission from `zinbo2024-bit` remains **COMMENTED**, not APPROVED. The review identifies missing verified identity/provider integration, server-derived role/checkpoint scope, durable production persistence/multi-worker guarantees, trusted audit attribution, notification/offline handling, and owner approvals. These gaps remain open; this note is not an independent security approval.

The checks above verify repository code and synthetic test behavior only. They do not authenticate callers, demonstrate trusted identity-to-role/checkpoint mapping, prove target-host behavior, demonstrate real notification delivery, authorize a field test, or establish production readiness.

**Release remains HOLD — NOT VERIFIED FOR PRODUCTION.** Keep PR #137 open and draft; do not merge or deploy. Continue using synthetic fixtures only, and never rely on this pilot as the sole emergency-response channel.
