# TGiTrailRun Pilot — Local Synthetic Verification Matrix

**Status:** READY TO RUN — results have not been recorded by this document.  
**Execution mode:** Local CLI/service only; synthetic fixtures only.  
**Release gate:** HOLD / NOT VERIFIED FOR PRODUCTION.

This matrix is for reproducible verification of the local pilot. Do not use real runner, medical, location, emergency-call, or live dispatch data. Passing this matrix does not establish production readiness.

## 1. Reproducible test commands

Use a clean checkout of the exact candidate commit on a Python 3.12 environment, matching CI. The repository workflow installs the JSON Schema validator explicitly.

```bash
python --version
git rev-parse HEAD
python -m pip install 'jsonschema>=4.18,<5'
python -m unittest discover -s tests -v
python -m compileall -q src tests scripts
git diff --check
```

Record the actual command output and exit status. A successful CI run must be linked to the exact commit SHA being evaluated. If the environment differs from CI, record the difference rather than treating the runs as equivalent.

## 2. Test matrix

| ID | Area | Test file / evidence target | Expected outcome | State |
|---|---|---|---|---|
| LV-01 | Data contract | `tests/test_tgi_trailrun_incident_contract.py` | Synthetic fixture validates against JSON Schema 2020-12; required fields, enum values, timezone-aware timestamps, and closed-object behavior are checked. | Pending execution record |
| LV-02 | State machine | `tests/test_trailrun_incident_state_machine.py` | Valid transitions pass; skipped, unknown, and no-op transitions fail closed without changing state. | Pending execution record |
| LV-03 | Role/action policy | `tests/test_trailrun_incident_access.py` | Unknown roles/actions deny by default; provisional role matrix is enforced by the policy helper. This does not authenticate a person. | Pending execution record |
| LV-04 | Persistence and idempotency | `tests/test_trailrun_incident_store.py` | Create/read works; exact duplicate is idempotent; changed payload under a reused event ID conflicts; state and audit persist atomically; denied transitions do not mutate; restart and concurrent duplicate scenarios are checked. | Pending execution record |
| LV-05 | Service boundary and scope | `tests/test_trailrun_incident_service.py` | Schema-invalid creation, reporter-role mismatch, unauthorized actions, and checkpoint out-of-scope create/read/audit/transition are rejected; denied transitions leave state/audit unchanged. | Pending execution record |
| LV-06 | Repository regression | Full suite via `python -m unittest discover -s tests -v` | All tests in the repository complete with exit code 0. Preserve test names and pass/fail/skip totals. | Pending execution record |
| LV-07 | Static/repository checks | Compile and whitespace checks above | Compilation and `git diff --check` complete successfully. | Pending execution record |
| LV-08 | Trusted identity / authentication | Not implemented in this local service boundary | **Blocked by design:** no selected network entry point or identity provider is evidenced. Do not report this as passed; do not treat caller-supplied role strings as identity. | Open blocker |
| LV-09 | Trusted checkpoint assignment | Identity adapter and owner-approved assignment source not implemented | **Blocked by design:** caller-supplied or constructor-injected scope is not proof of authenticated entitlement. | Open blocker |
| LV-10 | Live operational behavior | No live integrations or field rehearsal in scope | **Not run / out of scope:** no real dispatch, SMS/call delivery, responder timing, medical triage, or rescue outcome can be claimed. | Not authorized |

## 3. Evidence record template

Copy and complete this section for each actual run; do not fill it from expected results.

- Date/time and timezone:
- Operator / environment (local workstation or Codespace):
- Python version:
- Branch:
- Exact commit SHA:
- Exact command(s):
- Exit code:
- Tests run / passed / failed / skipped:
- Relevant output or attached log location:
- CI workflow run URLs for the same SHA:
- Environment differences, warnings, or failures:
- Open issues / owner:
- Release decision: **HOLD unless all relevant gates have explicit evidence and approval.**

Suggested shell capture, run from the repository root:

```bash
set -o pipefail
python -m unittest discover -s tests -v 2>&1 | tee local-test-output.log
test_exit=${PIPESTATUS[0]}
printf 'test_exit_code=%s\n' "$test_exit" | tee -a local-test-output.log
exit "$test_exit"
```

Keep logs free of secrets and real personal/medical data. A test log is evidence only when its recorded SHA matches the tested checkout.

## 4. Acceptance and stop rules

- [ ] The exact checkout SHA and environment are recorded.
- [ ] Full test-suite output and exit code are preserved.
- [ ] Negative tests prove denied requests do not mutate incident state, receipts, or audit records where covered.
- [ ] CI evidence refers to the same SHA as the local run.
- [ ] Failures are fixed and rerun; they are not waived by a different commit's green CI.
- [ ] Authentication, trusted identity-to-role derivation, and trusted checkpoint assignments remain explicitly open until a real entry point and provider are chosen and reviewed.
- [ ] Draft PR #137 is not merged and no deployment is performed as part of local verification.

**Decision rule:** A green local suite and green exact-head CI are necessary engineering evidence, not authorization for real data, live event use, merge, or production release. Keep the release at **HOLD / NOT VERIFIED FOR PRODUCTION** until independent security/privacy review and explicit race/event-owner approvals close the applicable gates.
