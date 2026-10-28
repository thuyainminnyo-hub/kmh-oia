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

## Latest exact-candidate CI evidence — 2026-10-28

The PR metadata currently identifies branch head `df4e2490683796cd7b63ae836712df6924aec772`, based on `032b588cc668c1edc309e8a8276253543427ac76`. For that head, GitHub Actions reports:

- [KMH OIA Tests #1070 — success](https://github.com/thuyainminnyo-hub/kmh-oia/actions/runs/40632764945). The run log recorded **503 tests, OK**, including the latest checkpoint-scope and initial-audit consistency cases.
- [KMH OIA Validation #989 — success](https://github.com/thuyainminnyo-hub/kmh-oia/actions/runs/40632764997). The run log recorded **503 tests, OK** and the validation workflow's static/repository validation steps completed successfully.
- GitHub PR metadata identifies `1fd5e02c517e26045b37b22844134b56fa39e612` as the generated merge-candidate SHA for head `df4e249...` and base `032b588...`. Keep this separate from the PR branch head SHA.

These results are GitHub Actions evidence for that candidate, **not** a local workstation/Codespace run. The local verification matrix remains unrecorded. Because this note is now being changed, the commit created by this edit needs its own CI verification before the evidence is treated as current for the updated head.

The latest reviewed code still does not authenticate callers or provide trusted identity-to-role/checkpoint mapping. No reviewer submission is currently recorded on PR #137. The release remains **HOLD / NOT VERIFIED FOR PRODUCTION**; do not merge, deploy, or use real runner/medical/location data.
