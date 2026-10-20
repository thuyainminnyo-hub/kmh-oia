# OIA-CASE-001 — Internal Project Brief Pilot

**Status:** Draft / CI validation pending  
**Workflow:** v1.0  
**Purpose:** Establish a traceable sample path from a project brief to a plan, requirements matrix, and QA checklist.  
**Data classification:** Synthetic example only; replace with an approved real brief before operational use.  
**Not a production claim:** CI validation checks repository artifacts only. It does not prove a live OIA runtime, external integrations, founder approval, or delivery.

## 1. Input manifest — INPUT-001

### Sample brief (assumptions for this pilot)
- **Project:** Internal request intake and delivery tracker
- **Objective:** Produce a lightweight plan to track requests from intake through review and delivery.
- **Users:** Internal team members (roles to be confirmed)
- **Requested outputs:** Project plan, requirements traceability matrix, QA checklist
- **Constraints:** No production deployment; no credentials or personal data in the sample; approval required before delivery.
- **Target timeline:** To be agreed; do not infer dates from this sample.
- **Budget / resources:** Not supplied; must be confirmed before commitment.
- **Acceptance expectation:** Each requirement maps to a planned output and a testable check.

### Input gaps / assumptions
1. Stakeholders and final approver are not named.
2. Timeline, effort, budget, hosting, retention, and access model are unknown.
3. “Delivery” means a reviewable internal artifact package until the owner defines otherwise.
4. This example is deliberately synthetic and is not evidence of a real customer request.

## 2. Output — PLAN-001

### Objective
Create a small, reviewable workflow specification for recording an internal request, checking required fields, tracking status, reviewing outputs, and recording a delivery decision.

### Proposed scope
**In scope**
- Define a minimal request record and lifecycle.
- Define mandatory fields and missing-information handling.
- Define acceptance criteria and traceability.
- Define QA and approval checkpoints.
- Record delivery receipt and outcome follow-up as separate states.

**Out of scope**
- Production deployment or live customer use.
- Authentication implementation, external integrations, and data migration.
- Claims of automation, monitoring, rollback, or runtime verification without separate evidence.

### Work plan
| Step | Work item | Deliverable | Exit condition |
|---|---|---|---|
| 1 | Confirm brief, stakeholders, and constraints | Locked input manifest | Owner confirms missing fields or records explicit N/A |
| 2 | Define lifecycle and required fields | Workflow specification | Each state and transition has an owner/condition |
| 3 | Map requirements to outputs and checks | TRACE-001 | Every requirement has an output and verification method |
| 4 | Review artifacts against QA checklist | QA-001 | All mandatory checks pass or have documented blockers |
| 5 | Obtain founder/authorized approver decision | Decision record | Exact artifact version approved or returned for changes |
| 6 | Deliver approved package | Delivery receipt | Destination, version, recipient, and timestamp recorded |
| 7 | Check expected outcome | Outcome record | Observed result and variance documented |

### Suggested lifecycle
`DRAFT → BRIEF CONFIRMED → PLAN READY → QA REVIEW → APPROVAL PENDING → APPROVED → DELIVERED → OUTCOME REVIEW`

A failed gate returns the work to the relevant earlier state. QA pass is not equivalent to approval. Approval applies only to the specific reviewed version.

## 3. Requirements traceability — TRACE-001

| Requirement ID | Requirement | Planned output | Verification | Current status |
|---|---|---|---|---|
| REQ-001 | Project objective and scope are explicit | PLAN-001 | Confirm objective and in/out-of-scope sections exist | Drafted from sample |
| REQ-002 | Unknowns are visible and not silently invented | INPUT-001 / PLAN-001 | Review assumptions and gaps list | Open — owner confirmation needed |
| REQ-003 | Each requirement maps to a test/check | TRACE-001 / QA-001 | Every REQ row has a verification method | Drafted |
| REQ-004 | Approval is distinct from QA | PLAN-001 / QA-001 | Confirm approval gate is separate | Drafted |
| REQ-005 | Delivery is tied to approved version | Delivery receipt template | Compare approved artifact version with receipt | Not run |
| REQ-006 | Outcome is reviewed after delivery | Outcome record template | Check observed outcome and variance fields | Not run |
| REQ-007 | Runtime evidence is not fabricated | Execution record | Require real run ID/logs from an actual run | Pending runtime execution |

## 4. QA checklist — QA-001

Mark a check **PASS** only after a reviewer verifies it. Until then, its status is **NOT RUN**.

| Check ID | Check | Pass condition | Status |
|---|---|---|---|
| QA-001 | Input completeness | Objective, scope, users, requested outputs, constraints are present or explicitly marked unknown | NOT RUN |
| QA-002 | Assumptions visibility | Unknown budget, schedule, roles, and environment are disclosed | NOT RUN |
| QA-003 | Traceability completeness | Each REQ has output and verification method | NOT RUN |
| QA-004 | Testability | Acceptance checks are observable and repeatable | NOT RUN |
| QA-005 | Approval separation | QA and approval are separate gates | NOT RUN |
| QA-006 | Version control | Input and output IDs/version can be recorded | NOT RUN |
| QA-007 | Evidence integrity | Run IDs/logs are real, linked, and not inferred from CI | NOT RUN |
| QA-008 | Delivery control | Delivery receipt references the approved artifact version | NOT RUN |
| QA-009 | Outcome follow-up | Expected vs observed outcome and variance can be recorded | NOT RUN |
| QA-010 | Sensitive data | Sample contains no secrets or unnecessary personal data | PASS — synthetic sample reviewed for this document |

## 5. Evidence record template

Fill only from observed events; never create placeholder IDs that look like real executions.

- **Case ID:** OIA-CASE-001
- **Input ID / version:** INPUT-001 / v0.1-sample
- **Repository:** https://github.com/thuyainminnyo-hub/kmh-oia
- **Branch:** case/oia-case-001-internal-brief
- **Commit SHA:** To be recorded after commit
- **CI run URL / conclusion:** To be recorded after GitHub Actions finishes
- **Runtime name / environment:** Pending confirmation
- **Execution ID / timestamp:** Pending real execution
- **Output versions:** PLAN-001 v0.1; TRACE-001 v0.1; QA-001 v0.1
- **QA reviewer / result:** Pending manual review
- **Founder/authorized decision:** Pending
- **Approved artifact version:** N/A until approval
- **Delivery receipt:** Pending
- **Outcome record:** Pending

## 6. Current gate assessment

| Gate | Assessment | Evidence / next action |
|---|---|---|
| G1 — Context | PARTIAL | Synthetic brief exists; owner, timeline, budget, and stakeholder confirmation remain open |
| G2 — Architecture | DRAFTED | Proposed lifecycle and artifacts documented; review required |
| G3 — Readiness | BLOCKED | Runtime/environment and approver not confirmed |
| G4 — Execution | NOT RUN | Need real runtime execution and execution record |
| G5 — Evidence & QA | NOT RUN | Manual QA must be performed; CI is not a substitute |
| G6 — Approval | PENDING | Authorized reviewer must decide on exact version |
| G7 — Delivery | NOT RUN | No delivery before approval |
| G8 — Outcome | NOT RUN | Requires delivery and subsequent observation |

## 7. Links
- Notion case record: https://app.notion.com/p/3f7fd51bf5758164b605c969290dfc54?pvs=204
- Repository: https://github.com/thuyainminnyo-hub/kmh-oia
- GitHub Actions: https://github.com/thuyainminnyo-hub/kmh-oia/actions

## 8. Next actions
1. Review and replace the synthetic sample with a real, non-sensitive brief.
2. Confirm owner, approver, scope, timeline, budget, and execution environment.
3. Let CI validate the repository change; record the exact run URL and conclusion.
4. Perform manual QA and record evidence.
5. Run the workflow in the confirmed runtime before marking G4 as proven.
6. Obtain approval before delivery; record outcome only after delivery.
