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

Record the actual command output and exit status. For pull-request workflows, distinguish the PR branch head SHA from the GitHub-generated merge-candidate SHA tested by Actions. Record both when they differ; do not claim SHA equality unless the checked-out revision proves it. If the environment differs from CI, record the difference rather than treating the runs as equivalent.

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
- Local checkout SHA (`git rev-parse HEAD`):
- PR branch head SHA, if applicable:
- CI workflow `GITHUB_SHA` / merge-candidate SHA, if applicable:
- Exact command(s):
- Exit code:
- Tests run / passed / failed / skipped:
- Relevant output or attached log location:
- CI workflow run URLs and the exact SHA each workflow tested:
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
- [ ] PR head SHA, CI-tested merge-candidate SHA, and local checkout SHA are recorded separately when different; any equality claim is verified from commit metadata.
- [ ] Failures are fixed and rerun; they are not waived by a different commit's green CI.
- [ ] Authentication, trusted identity-to-role derivation, and trusted checkpoint assignments remain explicitly open until a real entry point and provider are chosen and reviewed.
- [ ] Draft PR #137 is not merged and no deployment is performed as part of local verification.

**Decision rule:** A green local suite and green pull-request CI are necessary engineering evidence, not authorization for real data, live event use, merge, or production release. Keep the release at **HOLD / NOT VERIFIED FOR PRODUCTION** until independent security/privacy review and explicit race/event-owner approvals close the applicable gates.

## 5. CI SHA interpretation — verified example (2026-10-28)

This repository's pull-request workflows use `actions/checkout@v4` without setting an explicit `ref`. For the run associated with PR head `f071aafaae4035c4ff9b0a192c526e07c6a8d73d`, the evidence bundle records `4a3edbfefbab84800ad740406aeb337cd5ca7056`. GitHub metadata identifies `4a3edbf...` as the synthetic merge commit titled `Merge f071aaf... into 032b588...`. Therefore, the CI suite ran on the PR merge candidate, combining the candidate changes with the base; the two SHAs are related but not identical.

- [KMH OIA Tests #1065](https://github.com/thuyainminnyo-hub/kmh-oia/actions/runs/40626089238): job log says `Ran 500 tests ... OK`.
- [KMH OIA Validation #984](https://github.com/thuyainminnyo-hub/kmh-oia/actions/runs/40626089175): test job also says `Ran 500 tests ... OK`; compileall, deployment preflight, readiness snapshot, `git diff --check`, performance evidence, and deployment evidence bundle completed successfully.

This is valid integration CI evidence for that merge candidate, not a separate local workstation/Codespace run and not proof that the branch head SHA itself was checked out directly. The generated deployment bundle correctly describes its own `GITHUB_SHA` merge-candidate context; its SHA should not be relabeled as the PR branch head.

## Local evidence capture helper — added 2026-10-28

A Bash helper is available at [`scripts/capture_tgi_trailrun_local_verification.sh`](https://github.com/thuyainminnyo-hub/kmh-oia/blob/pilot/tgi-trailrun-runner-safety/scripts/capture_tgi_trailrun_local_verification.sh). Its syntax was checked with `bash -n` during preparation; it has not yet been run inside the user's Codespace.

Run this only from a clean checkout of the current PR #137 branch head. First confirm the current head SHA in GitHub. If the JSON Schema dependency is missing, install the documented test dependency explicitly before running the capture helper:

```bash
python -m pip install 'jsonschema>=4.18,<5'
bash scripts/capture_tgi_trailrun_local_verification.sh <current-pr-137-head-sha>
```

The helper refuses an invalid/missing SHA argument, records branch and local checkout SHA, checks that the working tree is clean and the checkout SHA exactly matches the supplied PR head, then captures the JSON Schema dependency check, full unittest suite, compilation, deployment preflight, and `git diff --check`. It does not install dependencies by itself, access network services, merge, or deploy. It writes a restrictive-permission, timestamped `.log` file in the repository root; the repository's `.gitignore` ignores `.log` files.

- A non-zero script exit means the evidence capture did not pass; inspect the recorded log and rerun after correcting the environment or checkout.
- A zero exit establishes only local engineering checks for that exact checkout. It does not verify identity authentication or trusted role/checkpoint mapping and is not production approval.
- Keep the output log private until it is reviewed for sensitive content. Use synthetic data only, and do not put real runner, medical, location, or emergency incident data in fixtures or logs.
