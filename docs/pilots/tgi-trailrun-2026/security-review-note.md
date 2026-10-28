# TGiTrailRun Runner Safety Pilot — Security Review Note

**Status:** HOLD / NOT VERIFIED  
**Scope:** Code review of the synthetic-data pilot on `pilot/tgi-trailrun-runner-safety`. This note is not event-owner approval or a production security certification.

## Verified evidence

- The latest inspected candidate commit `c326137f4173fa615a480aaee1121913d5253d02` has successful GitHub Actions runs:
  - Tests: https://github.com/thuyainminnyo-hub/kmh-oia/actions/runs/40623684589
  - Validation: https://github.com/thuyainminnyo-hub/kmh-oia/actions/runs/40623684350
- The service-boundary tests cover denial of volunteer dispatch, unchanged state/audit after denied action, role mismatch on create, and the configured role transitions.
- These results apply to that exact commit only. Subsequent changes require new exact-head CI evidence.

## Security gaps that remain open

1. **Authentication is not implemented here.** The `role` argument is caller-supplied. A real API must derive the role from a verified identity/session/token and must not trust a request-body role.
2. **Direct store calls can bypass the service policy.** `SQLiteIncidentStore.transition(..., actor_role=...)` accepts a role string and does not itself enforce the access policy. Production integration must make the service the only reachable write path or enforce authorization at the trusted service boundary with a private store layer.
3. **Resource-level scope is not implemented.** The current read methods do not constrain a caller to assigned checkpoints, incidents, or runner scope. Do not expose them to a network endpoint until scope checks are defined and tested.
4. **Role matrix is provisional.** Race director and medical lead must approve role-to-action mapping, especially who may acknowledge, dispatch, resolve, and close incidents.
5. **Schema validation is a caller responsibility.** Validate the complete incident payload with the published JSON Schema before passing it to the store.
6. **Persistence is local SQLite only.** No evidence yet for multi-host deployment, production backup/restore, disaster recovery, or multi-replica concurrency.
7. **No live dispatch/notifications or emergency service integration exists.** Do not describe this pilot as a rescue dispatch system.

## Required security acceptance tests

- Unauthenticated request is denied.
- Request-body role spoofing is denied.
- Volunteer cannot dispatch through any public or internal write path.
- A caller cannot read an incident or audit record outside their approved scope.
- Unauthorized attempts leave status, receipt, and audit records unchanged.
- Invalid schema payloads are rejected before persistence.
- Audit log contains a trusted actor identifier, not just a free-form role.
- CI is green for the exact candidate commit.
- Race director, medical lead, privacy owner, and security reviewer sign off before any real data or field trial.

## Release decision

**HOLD / NOT VERIFIED.** Do not merge as production-ready, deploy, or use real runner/medical data until the open gaps and Gate C/D requirements in `runner-safety-pilot.md` have evidence and explicit owner approval.
