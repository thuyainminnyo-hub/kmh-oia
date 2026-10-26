# Landscape Design Intelligence Pilot

**Status:** Specification draft — not implemented or independently verified.  
**Scope:** Site intake and evidence registry through design QA.  
**Repository base:** `032b588cc668c1edc309e8a8276253543427ac76`  
**Related tracking:** [Issue #118](https://github.com/thuyainminnyo-hub/kmh-oia/issues/118)

## 1. Goal and boundaries

Create a deterministic, traceable workflow that helps a landscape design learner or reviewer organize site evidence, map requirements to design options, and assess design work against a versioned rubric. The pilot must not invent site measurements, imply that an assumption is verified, or replace professional review.

The current KMH OIA runtime exposes a deterministic local runtime, injectable state boundary, tool security policy, and tracer interface. The README states default state is in-memory and local JSON persistence is not a production database. This pilot must integrate through existing boundaries and must not imply durable production telemetry or deployment.

## 2. Workflow

1. **Intake:** accept a project brief, site boundary reference, area and units, intended use, constraints, jurisdiction and source artifacts.
2. **Registry:** record observations and provenance for topography, sun/shade, drainage, climate, vegetation, access, utilities and hazards.
3. **Validation:** reject invalid units/ranges; flag required fields that are absent; record source dates and limitations.
4. **Analysis:** generate deterministic summaries from supplied evidence. Mark unverified values as assumptions and keep them separate from observations.
5. **Design options:** map requirements to concept references, rationale, linked observations, constraints and assumptions.
6. **Representation:** record versioned plan, section, sketch and presentation references.
7. **QA:** run a versioned rubric and return PASS, HOLD or FAIL with criterion-level findings.
8. **Trace:** link each run to input/output references, schema/rubric version, events, errors and reviewer decision.
9. **Learning:** feedback may become a proposed rule/test only after human approval and regression coverage.

## 3. Proposed registry entities

| Entity | Required fields |
|---|---|
| Project | project_id, name, site_id, brief_version, status, created_at |
| Site | site_id, boundary_ref, area_value, area_unit, jurisdiction, source_refs |
| Observation | observation_id, site_id, category, value, unit, observed_at, source_ref, method, confidence, limitations |
| Requirement | requirement_id, project_id, statement, priority, acceptance_test, source_ref, status |
| DesignOption | option_id, project_id, version, concept_ref, rationale, linked_observations, assumptions, author, created_at |
| QAResult | qa_id, option_id, rubric_version, criterion_results, status, findings, reviewer_role, reviewed_at |
| Evidence | evidence_id, entity_type, entity_id, artifact_uri, content_hash, source_type, captured_at, provenance, access_class |
| RunEvent | run_id, event_type, input_refs, output_refs, policy_version, started_at, finished_at, result, error_code |

Use synthetic fixtures until access, retention and handling rules for client site data are approved. Do not commit secrets or confidential site documents.

## 4. QA gate

- **PASS:** every mandatory requirement is evidenced; units and provenance are present; critical constraints are reviewed; rubric criteria pass; no unresolved high-severity issue remains.
- **HOLD:** evidence is missing or stale, assumptions remain unverified, requirements conflict, or a required professional review is pending.
- **FAIL:** a mandatory criterion demonstrably fails, invalid data was accepted, or a safety-critical contradiction exists.

A QA result must include criterion IDs, result, evidence references, rationale, rubric version and reviewer role. Where appropriate, final sign-off remains with a qualified landscape architect or other responsible professional. AI output is not survey, engineering or regulatory sign-off.

## 5. KPI definitions

Targets are **TBD until baseline data exists**.

- Site data completeness = valid populated mandatory fields / all mandatory fields.
- Provenance coverage = evidence-backed material claims / all material claims.
- Requirement coverage = requirements mapped to a design/QA criterion / all requirements.
- QA first-pass rate = options passing first review / options reviewed.
- Defect escape rate = critical defects discovered after PASS / all critical defects discovered.
- Revision improvement = rubric score delta between reviewed versions.
- Trace completeness = runs with all required trace fields / total runs.

Record denominator, measurement window, dataset version and exclusions for every reported KPI. Do not report percentages without observations and reproducible calculation.

## 6. Minimum test matrix

| ID | Input / scenario | Expected behavior |
|---|---|---|
| T01 | Valid synthetic site input | normalized record and run identifier |
| T02 | Missing boundary or units | HOLD with missing-field list |
| T03 | Invalid numeric value or unsupported unit | reject; no silent coercion |
| T04 | Missing/stale material source | provenance warning and HOLD |
| T05 | Unsupported sun/drainage claim | label as assumption or reject as unsupported |
| T06 | Conflicting requirements | HOLD with conflict list |
| T07 | Mandatory rubric criterion fails | FAIL with criterion evidence |
| T08 | All mandatory checks pass and reviewer evidence exists | PASS |
| T09 | Required reviewer is absent | HOLD |
| T10 | Input changes after QA | prior result becomes stale; rerun required |
| T11 | Required trace field absent | test fails |
| T12 | Unauthorized private artifact access | deny and emit security event |
| T13 | Same input and same rules | stable normalized output (excluding generated IDs/timestamps) |
| T14 | Feedback proposes a new rule | no promotion without approval and regression test |

## 7. Acceptance criteria

- Schema, rubric and synthetic fixtures are versioned.
- Missing/stale evidence is flagged; invalid units/ranges are rejected.
- Every run links input, output, schema/rubric version, events and QA outcome.
- Automated tests cover PASS/HOLD/FAIL, negative cases, determinism and trace completeness.
- Every material claim has source evidence or an explicit assumption label.
- QA is repeatable for unchanged inputs and rules.
- No secrets or confidential site data exist in fixtures/artifacts.
- CI passes on the exact candidate commit and run/artifact references are retained.
- Independent review is submitted against the exact candidate SHA before merge.
- Production remains HOLD until target-host persistence, access controls, backup/restore, monitoring and operational evidence are separately verified.

## 8. Implementation sequence

- **P0 — Discovery:** inspect architecture, tests, security, state and trace interfaces; record exact base SHA.
- **P1 — Specification:** publish this document and align issue/Notion evidence.
- **P2 — Registry:** implement typed data structures and validation only.
- **P3 — Analysis:** deterministic evidence-grounded summaries and assumption labelling.
- **P4 — QA:** versioned rubric and PASS/HOLD/FAIL engine.
- **P5 — Trace:** use existing trace boundary; do not bypass security or claim durable telemetry.
- **P6 — Tests:** unit, negative, regression, determinism, trace and access-control tests.
- **P7 — Evidence:** run locally and in CI; retain exact SHA, logs and artifacts.
- **P8 — Review:** independent review, fix findings, and keep release gate closed until all evidence supports promotion.

## 9. Evidence checklist

- [ ] Base SHA and working-tree state recorded
- [ ] Schema and rubric versioned
- [ ] Synthetic fixtures and expected outputs committed
- [ ] Unit/negative/regression tests pass on exact SHA
- [ ] CI URL, run ID, artifact ID and test summary recorded
- [ ] Example trace links inputs, outputs and rubric version
- [ ] QA result contains criterion-level evidence and reviewer role
- [ ] No secrets or private site data in repository/artifacts
- [ ] Independent review submitted on exact SHA
- [ ] Production controls separately evidenced; otherwise HOLD

## 10. Current state (P2 update — 2026-10-26)

- **Implemented in this branch:** typed registry dataclasses for project, site, observation, requirement, design option, evidence, QA result and run event; site/observation payload validation; required-field, numeric-range, unit, category-unit compatibility, ISO-date, confidence and provenance checks; synthetic-only fixture; automated negative/positive tests.
- **Verified:** GitHub Actions `KMH OIA Tests` run [#928](https://github.com/thuyainminnyo-hub/kmh-oia/actions/runs/40331536222) completed successfully for candidate head `3db6bbf1b8fd4ddaca8559788f388b53e2a7c4fc`. `KMH OIA Validation` run [#847](https://github.com/thuyainminnyo-hub/kmh-oia/actions/runs/40331536378) also completed successfully for that same candidate head. Both workflows ran `python -m unittest discover -s tests -v` successfully; validation also passed compileall, deployment preflight, diff check and evidence-bundle checks. A later documentation-only commit may trigger another CI run; the code under test is unchanged.
- **Not implemented:** site-analysis engine, QA decision engine, OIA trace integration, stale-source policy, and end-to-end landscape workflow.
- **Not established:** independent review, merge, deployment, production readiness or professional design sign-off.

This work does not modify PR #103, authorize a merge, or change the existing production HOLD.
