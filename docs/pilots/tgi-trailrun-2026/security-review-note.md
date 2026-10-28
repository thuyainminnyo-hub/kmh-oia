# TGiTrailRun Runner Safety Pilot — Security Review Note

**Status:** HOLD / NOT VERIFIED  
**Scope:** Code review of the synthetic-data pilot on `pilot/tgi-trailrun-runner-safety`. This note is not event-owner approval or a production security certification.

## Verified evidence

- Earlier candidate commit `c326137f4173fa615a480aaee1121913d5253d02` passed Tests and Validation:
  - Tests: https://github.com/thuyainminnyo-hub/kmh-oia/actions/runs/40623684589
  - Validation: https://github.com/thuyainminnyo-hub/kmh-oia/actions/runs/40623684350
- The current candidate adds store-boundary transition authorization and service-boundary JSON Schema validation with negative tests.
- Exact-head CI for the current candidate is in progress; do not treat earlier green runs as evidence for the latest changes.

## Security gaps that remain open

1. **Authentication is not implemented here.** The `role` argument is caller-supplied. A real API must derive the role from a verified identity/session/token and must not trust a request-body role.
2. **Caller-supplied role is still not trusted identity.** The store now checks the role/action policy for transitions as defense in depth, but `actor_role` remains a string supplied by the caller. A real API must derive role from a verified identity and must not trust request-body roles.
3. **Resource-level scope is not implemented.** The current read methods do not constrain a caller to assigned checkpoints, incidents, or runner scope. Do not expose them to a network endpoint until scope checks are defined and tested.
4. **Role matrix is provisional.** Race director and medical lead must approve role-to-action mapping, especially who may acknowledge, dispatch, resolve, and close incidents.
5. **Schema validation is enforced at the service create boundary, but not every direct store call.** Network-facing integrations must only expose the service boundary, and the storage layer should eventually be made private or independently validate complete payloads.
6. **Persistence is local SQLite only.** No evidence yet for multi-host deployment, production backup/restore, disaster recovery, or multi-replica concurrency.
7. **No live dispatch/notifications or emergency service integration exists.** Do not describe this pilot as a rescue dispatch system.

## Required security acceptance tests

- Unauthenticated request is denied.
- Request-body role spoofing is denied.
- Volunteer cannot dispatch through any public or internal write path.
- A caller cannot read an incident or audit record outside their approved scope.
- Unauthorized attempts leave status, receipt, and audit records unchanged.
- Invalid schema payloads are rejected by the service before persistence.
- Direct store transition calls cannot use a disallowed role/action transition.
- Audit log contains a trusted actor identifier, not just a free-form role.
- CI is green for the exact candidate commit.
- Race director, medical lead, privacy owner, and security reviewer sign off before any real data or field trial.

## Release decision

**HOLD / NOT VERIFIED.** Do not merge as production-ready, deploy, or use real runner/medical data until the open gaps and Gate C/D requirements in `runner-safety-pilot.md` have evidence and explicit owner approval.
