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

## Latest exact-head CI evidence before this review-document refresh — 2026-10-29

The last fully verified source candidate before this review-document refresh is `eaf37e540af3bac02452f8e21db80c7c3e2ac80b`. The documentation-only commit that follows still requires its own CI run; do not describe the parent run as verification of the later SHA.

- [KMH OIA Tests #40822856450 — success](https://github.com/thuyainminnyo-hub/kmh-oia/actions/runs/40822856450). The exact-candidate test log records **517 tests, OK** (`Ran 517 tests in 1.020s`). The strengthened `test_file_database_survives_store_recreation` test ran in this suite.
- [KMH OIA Validation #40822856444 — success](https://github.com/thuyainminnyo-hub/kmh-oia/actions/runs/40822856444). The tests, repository-validation, performance-evidence, and deployment-evidence-bundle jobs completed successfully.
- The corresponding local verification matrix documents the restart/replay expectations: incident status and embedded/authoritative audit remain consistent after reopening the database; the original idempotency receipt survives; a changed payload for the same event remains a conflict; and replay/conflict do not append audit history.

An earlier local Colab verification was reported for commit `4cc4499144d951ae0cf9f5b492d3b1d508db58e0` (Python 3.12.3, 514 tests, compile/preflight/diff checks passed). That run is not an exact-head local run for `eaf37e5...`; no local checkout execution at the latest candidate is evidenced here.

The formal reviewer submission from `zinbo2024-bit` remains **COMMENTED**, not APPROVED. The review identifies missing verified identity/provider integration, server-derived role/checkpoint scope, durable production persistence/multi-worker guarantees, trusted audit attribution, notification/offline handling, and owner approvals. These gaps remain open; this note is not an independent security approval.

The checks above verify repository code and synthetic test behavior only. They do not authenticate callers, demonstrate trusted identity-to-role/checkpoint mapping, prove target-host behavior, demonstrate real notification delivery, authorize a field test, or establish production readiness.

**Release remains HOLD — NOT VERIFIED FOR PRODUCTION.** Keep PR #137 open and draft; do not merge or deploy. Continue using synthetic fixtures only, and never rely on this pilot as the sole emergency-response channel.

