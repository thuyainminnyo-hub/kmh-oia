# OIA-CASE-001 — Local Run Readiness Checklist

**Status:** SCOPE APPROVED / READINESS PENDING / NOT RUN  
**Last updated:** 2026-10-16  
**Purpose:** Prepare a reproducible, local-only synthetic-data run without implying execution occurred.

## Approved scope
- Approval received in conversation on 2026-10-16 at 14:07:13Z.
- Approver identity supplied by user: Kyaw Min Han (kyawminhan2024@gmail.com); identity/role not independently verified.
- Input: synthetic/test data only.
- Runtime: local environment only.
- Permitted tools: repository checks and local test tools only.
- Excluded unless separately approved: production data/credentials/access, external integrations, production changes, and any tool outside the agreed repository/local-test scope.
- Stop condition: stop immediately and record the event if unexpected output, an error, an out-of-scope action, or possible sensitive-data exposure occurs.
- Durable decision record: GitHub issue #74 and PR #73 scope-approval comment.

## Gate A — Explicit scope authorization
- [x] Explicit statement approving the exact synthetic/test-data-only, local-runtime, local-checks/tests scope.
- [x] Record the user-provided approver identity and timestamp; identity/role remain unverified.
- [x] Approval explicitly excludes production data/credentials, external integrations, and production changes unless separately approved.
- [ ] If governance policy requires independent/separate approver verification, link the policy and obtain that verification.

**Gate A status: APPROVED (scope only).**

## Gate B — Local runtime readiness
- [ ] Identify the local machine/runner and operating-system/runtime versions.
- [x] Locate the documented commands in `README.md` (documentation verified on this PR branch): runtime smoke `python -m src.main "hello"`; test suite `python -m unittest discover -s tests -v`. These are documented candidates only; neither command has been run for this case, and execution remains on hold until the other Gate B items are verified.
- [ ] Confirm dependencies and configuration versions.
- [ ] Confirm no production credentials or external integrations are enabled.
- [ ] Confirm synthetic fixture/input path, approved version, and hash.
- [ ] Confirm output path and access permissions.
- [ ] Confirm log/evidence storage path and retention/access controls.

**Gate B status: PENDING.** Runtime access/configuration, approved fixture/version/hash, and output/log locations are not verified. No runtime command has been executed for this case.


## Access constraint — phone-only workflow
- User confirmed on 2026-10-16 that they currently have phone-only access.
- A local workstation/runner and its OS/Python versions are therefore not available for verification through the current workflow.
- Continue documentation, review, and readiness tracking from GitHub using the phone.
- Do not substitute GitHub-hosted Actions, a cloud runner, or an unreviewed online execution service for the approved local-runtime scope.
- Runtime smoke test and unit tests remain **NOT RUN** for this case. Repository CI is not evidence of local runtime execution.
- Revisit Gate B only if a suitable local execution environment becomes available and its isolation, configuration, synthetic fixture/hash, output path, and evidence/log locations can be verified. Any change from local-only execution requires separate scope review/approval first.

## Gate C — Execution and evidence
Before starting:
- [ ] Capture commit SHA, branch, input manifest/hash, environment details, and start timestamp.
- [ ] Confirm the stop condition and who can stop the run.
- [ ] Verify the run is local and cannot send data externally.

During/after a real run:
- [ ] Record actual command, exit status, run identifier if available, start/end timestamps.
- [ ] Preserve relevant logs and output manifest/hash.
- [ ] Record errors, unexpected behavior, and any stop events.
- [ ] Complete QA against intended behavior; record reviewer and findings.
- [ ] Do not label the case successful until evidence is reviewed and acceptance criteria pass.

## Evidence record
Use `execution-record-template.md` and fill only observed facts. Use `NOT RUN`, `PENDING`, or `NOT VERIFIED` for unknowns. Never fabricate run IDs, logs, timestamps, outputs, QA results, or approvals.

## Current decision
**APPROVED SCOPE / HOLD FOR READINESS / NOT RUN.** Scope authorization is recorded, but this is not a GO decision. Repository CI results do not prove that a local runtime execution occurred. Do not execute until remaining readiness gates are verified and recorded.
