# KMH Prompt Library Versioning + QA Pilot v1.0

**Pilot ID:** `KMH-DATA-PILOT-001`  
**Parent contract:** KMH Reusable Data Governance Blueprint v1.0  
**Status:** SPECIFICATION READY — NOT IMPLEMENTED / NOT RUNTIME VERIFIED  
**Scope:** One bounded Prompt Library dataset; no changes to `KMH-RUN-001` runtime status.

## 1. Objective
Prove that a KMH prompt can be identified, versioned, validated, reviewed, approved, released, and traced without silently replacing canonical content or treating a draft as trusted memory.

## 2. Minimum Record Contract
Each prompt record should contain:

| Field | Requirement | Meaning |
|---|---|---|
| `prompt_id` | Required, stable | Identity that survives prompt edits |
| `version` | Required | Immutable version, e.g. `1.0.0` |
| `title` | Required | Human-readable name |
| `purpose` | Required | Task the prompt is designed for |
| `prompt_text` | Required | Exact prompt content for this version |
| `input_contract` | Required | Expected input fields, types, and constraints |
| `expected_output` | Required | Output structure or acceptance criteria |
| `target_model_or_tool` | Required | Intended execution target; record unknowns explicitly |
| `status` | Required | `DRAFT`, `IN_REVIEW`, `APPROVED`, `PUBLISHED`, `REJECTED`, `RETIRED` |
| `change_summary` | Required after v1 | What changed and why |
| `test_cases` | Required before approval | Representative normal, edge, and failure cases |
| `test_evidence` | Required before approval | Actual results or explicit `NOT RUN` |
| `proposed_by` | Required | Contributor or automation identity |
| `reviewed_by` | Required for approval | Reviewer identity or `NOT REVIEWED` |
| `approved_by` | Required for publication | Authorized approver or `NOT APPROVED` |
| `created_at` | Required | Timestamp with timezone where available |
| `source_refs` | When applicable | Supporting source or case-study links |

## 3. Versioning Rules
- First controlled release starts at `1.0.0` only after approval; working drafts may use `0.x`.
- Major version: incompatible task/input/output contract change.
- Minor version: backward-compatible capability or instruction change.
- Patch version: narrow correction that does not intentionally change the contract.
- Every published version is immutable. Edits create a new version and changelog entry.
- The active alias (for example, `production-approved`) must point to a specific published version, never to a moving draft.
- Do not claim semantic-version compatibility until tests support the claim.

## 4. QA Test Matrix

| Test | Expected | Failure handling |
|---|---|---|
| Required fields | All required metadata present | Block review |
| Stable ID | `prompt_id` remains the same across revisions of the same prompt | Flag duplicate/new identity confusion |
| Version uniqueness | No two records share the same `prompt_id` + `version` | Block release |
| Input contract | Valid inputs are accepted; invalid inputs are surfaced | Revise prompt or contract |
| Output contract | Actual output meets declared structure/criteria | Record FAIL and revise |
| Normal case | Representative common task passes | No approval until resolved |
| Edge case | Missing/ambiguous/long input handled according to policy | Document limitation or revise |
| Failure case | Prompt does not invent unavailable evidence; uncertainty is explicit | Fail if unsupported claims are asserted |
| Regression | Existing approved test cases remain within acceptance criteria | Block release or document authorized breaking change |
| Evidence trace | Each test records prompt version, input fixture, actual output, verdict, and run reference if available | Mark `NOT RUN` when absent; never fabricate |
| Human review | Reviewer decision is explicit | Remain `IN_REVIEW` |
| Publication | Approved immutable version and changelog are identifiable | Do not mark `PUBLISHED` |

## 5. Lifecycle
`DRAFT → VALIDATING → IN_REVIEW → APPROVED → PUBLISHED`

Other valid states: `NEEDS_CHANGES`, `REJECTED`, `RETIRED`.

A schema check is not a behavior test. A behavior test is not human approval. Human approval is not proof of production execution. Production use requires separate execution evidence.

## 6. Evidence Record
For each test execution, capture where available:
- `test_run_id`
- `prompt_id` and exact `version`
- `input_fixture_ref` (avoid storing secrets or unnecessary personal data)
- `actual_output_ref` or sanitized output
- `expected_criteria`
- `verdict`: `PASS`, `FAIL`, or `NOT RUN`
- `timestamp`
- `model_or_tool_version` and relevant configuration
- `reviewer_note`

Never label a test `PASS` without inspecting the actual output against the declared criteria. If no model/tool execution occurred, mark behavior testing `NOT RUN`.

## 7. Pilot Exit Criteria
The pilot may be called **GOVERNANCE-DESIGNED** when this contract and lifecycle are accepted.
It may be called **IMPLEMENTED** only when records, version controls, validators, and release states exist in the chosen system and are inspectable.
It may be called **RUNTIME VERIFIED** only after real test executions produce inspectable evidence and the evidence is reviewed.
It may be called **OPERATIONAL** only after the owner explicitly approves the release process and the acceptance criteria pass.

## 8. Smallest Safe First Run
1. Select one existing low-risk prompt; preserve its original text.
2. Assign a stable `prompt_id` and create a draft record.
3. Define input and output acceptance criteria before testing.
4. Prepare one normal case, one edge case, and one failure case.
5. Run tests only in an available, authorized environment; otherwise leave them `NOT RUN`.
6. Compare actual output with expected criteria and log failures.
7. Obtain explicit review/approval before publication.
8. Publish a versioned snapshot and changelog only when the evidence gate passes.

## 9. Current Gate
- Specification: `CREATED`.
- Prompt selected: `NOT SELECTED`.
- Validator implemented: `NOT VERIFIED`.
- Behavioral tests: `NOT RUN`.
- Approval: `NOT APPROVED`.
- Published production prompt: `NONE FROM THIS PILOT`.

**Next action:** select one existing prompt and capture its exact text and intended use, then create the first draft record. This specification does not change `KMH-RUN-001 = READY / CAPACITY BLOCKED / NOT EXECUTED`.
