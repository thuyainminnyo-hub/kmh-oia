# OIA-CASE-001 — Local Run Readiness Checklist

**Status:** PROPOSED / NOT AUTHORIZED / NOT RUN  
**Last updated:** 2026-10-15  
**Purpose:** Prepare a reproducible, local-only synthetic-data run without implying approval or claiming execution occurred.

## Proposed scope (not yet approved)
- Input: synthetic/test data only.
- Runtime: local environment only.
- Permitted tools: repository checks and local test tools only.
- Prohibited unless separately approved: production access, external integrations, real/sensitive user data, outbound delivery, and any tool outside the agreed repository/local-test scope.
- Stop condition: stop immediately and record the event if unexpected output, an error, an out-of-scope action, or possible sensitive-data exposure occurs.

## Gate A — Explicit scope authorization
- [ ] Case owner provides an explicit statement approving this exact scope.
- [ ] Record the author/identity, timestamp, and durable approval location.
- [ ] If the governance policy requires a separate approver, link the policy and obtain that approval too.
- [ ] Approval explicitly excludes production access and external integrations.

**Gate A status: PENDING.** A request to “continue” or an ambiguous confirmation is not approval of this scope.

## Gate B — Local runtime readiness
- [ ] Identify the local machine/runner and operating-system/runtime versions.
- [ ] Confirm the exact command(s) to run from repository documentation; do not invent commands.
- [ ] Confirm dependencies and configuration versions.
- [ ] Confirm no production credentials or external integrations are enabled.
- [ ] Confirm synthetic fixture/input path and version/hash.
- [ ] Confirm output path and access permissions.
- [ ] Confirm log/evidence storage path and retention/access controls.

**Gate B status: PENDING.** Runtime access and configuration have not been verified by this checklist.

## Gate C — Execution and evidence
Before starting:
- [ ] Capture commit SHA, branch, input manifest/hash, environment details, and start timestamp.
- [ ] Confirm the stop condition and who can stop the run.
- [ ] Confirm the run is offline/local and cannot send data externally.

During/after a real run:
- [ ] Record actual command, exit status, run identifier if available, start/end timestamps.
- [ ] Preserve relevant logs and output manifest/hash.
- [ ] Record errors, unexpected behavior, and any stop events.
- [ ] Complete QA against the intended behavior; record reviewer and findings.
- [ ] Do not label the case successful until evidence is reviewed and acceptance criteria pass.

## Evidence record
Use `execution-record-template.md` and fill only observed facts. Use `NOT RUN`, `PENDING`, or `NOT VERIFIED` for unknowns. Never fabricate run IDs, logs, timestamps, outputs, QA results, or approvals.

## Current decision
**HOLD / NOT RUN.** This checklist is preparation only. Repository CI results do not prove that a local or live runtime execution occurred.
