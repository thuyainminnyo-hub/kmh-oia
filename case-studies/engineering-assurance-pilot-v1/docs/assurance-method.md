# Assurance Method & Decision Rules

## Evidence standard
Every confirmed finding must identify a repository path, line range where possible, immutable commit, reproducible observation, impact path, and evidence reference. A claim inferred only from a filename, tool output, model opinion, or historical summary is not a confirmed vulnerability.

## Independent challenge
A second reviewer must challenge:
- reachability and preconditions;
- exploitability or operational impact;
- affected versions/configurations;
- counter-evidence and compensating controls;
- whether the proposed fix introduces a different risk.

The author of a finding or remediation cannot be its sole independent verifier. If reviewer independence cannot be established, record BLOCKED.

## Classification
- CONFIRMED: evidence demonstrates the issue and impact path.
- NEEDS_VALIDATION: plausible but missing a reproducible prerequisite or impact proof.
- ACCEPTED_RISK: authorized human owner accepts a documented trade-off with rationale, expiry/review date, and compensating controls.
- REJECTED_FALSE_POSITIVE: counter-evidence demonstrates why the claim does not hold.

Severity is separate from status. Never silently downgrade severity to make a gate pass.

## Risk-based decisions
Critical: stop release; High: fix or explicit owner-approved exception with compensating controls; Medium: prioritize and schedule; Low/Info: document. A Critical or High unresolved item blocks the QA gate.

## Human authority
Agents may propose and challenge. Only the designated human owner may accept risk, approve release, or authorize scope expansion. A CI green check is not human approval.

## QA Gate
The package validator checks structure only. Domain assessment, tests, independent review, human approval, and rollback readiness each require separate evidence. The overall gate remains BLOCKED until all mandatory evidence is attached.

## Rollback
For this documentation/validator-only pilot, rollback means reverting the assurance-only feature branch commit(s). Preserve the base branch and existing PR #185. Do not delete historical evidence or rewrite shared history. Production rollback is out of scope because no production change is permitted.
