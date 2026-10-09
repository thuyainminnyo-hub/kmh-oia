# Case Study — YBS Route Data Governance & Single Source of Truth

**Classification:** Data Governance / Version Control / Public Data Infrastructure  
**Decision:** ACCEPT WITH REFINEMENTS  
**Evidence status:** Analysis of user-supplied case study; original app, code, and dataset not independently inspected.

## 1. Executive Summary
The case describes a route editor intended to make bus routes easier to create and update, compare old and new versions, and exchange datasets through local storage and JSON import/export. Its long-term vision is a central data hub consumed by multiple YBS apps.

The central lesson: a route editor helps people edit data, but does not by itself establish data correctness or a single source of truth. A trustworthy shared dataset also needs stable identifiers, provenance, version history, validation, review and approval, effective dates, and controlled publication.

## 2. Problem Statement
- Route data appears inconsistent across sources and applications.
- Routes and stops may change over time.
- Base map geometry is not proof that a bus operates along that path.
- Local storage and JSON exchange allow sharing, but do not provide one synchronized canonical dataset.
- Without version and approval controls, consumers may unknowingly use conflicting route data.

## 3. Described App Capabilities
Based on the supplied post, not an independent code review:
- Visual route creation and stop selection.
- Distance-based stop suggestions.
- Comparison of previous and updated routes.
- Local storage.
- JSON export/import for sharing and merging changes.

These are useful editing and exchange capabilities. They are not proof that data is correct, centrally governed, or actively consumed by production YBS apps.

## 4. SSOT Is Governance, Not Just a Server
A central server is useful, but a Single Source of Truth also requires clear answers to: which version is canonical; who may propose changes; what evidence supports a change; which validations must pass; who approves publication; when a version takes effect; how bad versions are withdrawn or rolled back; and which dataset version downstream apps consumed.

Recommended flow:
Contributor proposal → Draft/version history → Automated validation → Human review and evidence → Approval → Canonical published dataset → API/export → Consumer apps.

Draft data and approved public data must remain separate. Community voting can express feedback, but votes alone do not prove route accuracy.

## 5. Suggested Data Model
### Route
- route_id: stable identifier, not derived only from a route label.
- route_name / route_code; operator where known.
- status: draft / in_review / approved / retired.
- current_approved_version; effective_from; effective_until; source references.

### Route Version
- route_id; immutable version identifier; ordered_stop_ids; geometry; direction/variant.
- change_summary; proposed_by; proposed_at; reviewed_by; approved_by; approval_status.
- effective_from; evidence references; schema_version.

### Stop
- stop_id: stable identifier; name and aliases; coordinates.
- source provenance; verification status; last checked date.

### Evidence / Change Record
- evidence type and source; captured/reported date; route/version; reviewer decision; audit trail.

These are recommendations, not claims about fields already present in the original app.

## 6. Validation and QA Rules
- Validate imported JSON against a versioned schema before accepting it.
- Check unique IDs, required fields, coordinate ranges, and ordered stop references.
- Detect duplicate or near-duplicate stops without automatically merging uncertain matches.
- Compare geometry against stop sequence and flag implausible jumps; do not infer operational truth from map geometry alone.
- Preserve provenance and the reason for each change.
- Mark unsupported changes UNVERIFIED; do not publish them as approved facts.
- Require review for material route changes.
- Keep immutable version history and support rollback.
- Record publication timestamp and exact dataset version served to consumers.

## 7. Interoperability and Public API
A future central hub could expose a documented API, versioned snapshots and change feeds, JSON downloads for offline use, schema/version metadata, last-updated and verification status, and deprecation/rollback notices.

For public adoption, define licensing, attribution, contribution policy, rate limits, uptime expectations, and error reporting. An API does not solve source accuracy unless the upstream review and update process is reliable.

## 8. Risks and Mitigations
| Risk | Mitigation |
|---|---|
| Incorrect community edit | Review, evidence and status separation |
| Conflicting JSON files | Schema validation, stable IDs, explicit merge/conflict review |
| Stale approved route | Effective dates, last-verified metadata, stale-data alerts |
| Map path mistaken for real service | Distinguish base-map geometry from verified operational route |
| Central hub becomes a bottleneck | Clear reviewer roles, audit trail, correction and rollback workflow |
| Consumers cache old data | Dataset version identifiers and change notifications |

## 9. KMH Operating Organism Reuse
- Brain / Operating Intelligence Architecture: define trust, approval, promotion, and rollback rules.
- Memory: preserve canonical data, immutable versions, source provenance, and validated learning.
- Nervous System: notify downstream consumers when approved data changes.
- Immune System: reject invalid schema, missing provenance, conflicting IDs, or unapproved publication.
- Execution layer: validate, merge, publish, export, and monitor the dataset.
- Evidence contract: every important change links to source evidence and a review decision.

Preserve the architecture distinction: Operating Intelligence Architecture is the Brain; KMH Operating Organism is the whole system.

## 10. Reusable Decision
ACCEPT WITH REFINEMENTS as a case study in versioned public data governance.

Do not classify the described app as a verified central source of truth: the supplied post says the current version stores data locally and supports JSON import/export, while the central backend is a future plan.

## 11. Next Actions
1. Inspect the actual app repository and sample JSON schema before making implementation claims.
2. Define a versioned route/stop schema and validation rules.
3. Define contribution, review, approval, effective-date, and rollback states.
4. Prototype an immutable dataset release and JSON export.
5. Then design the central API and downstream-consumer integration.
6. Verify with real examples and evidence before claiming the dataset is operationally authoritative.

## 12. Evidence Boundary
This case study is based on the user-supplied description. No original application code, route dataset, backend, operational bus records, or production API were inspected. Current app features are attributed to the supplied post; architecture additions are recommendations, not verified implementation facts.

**KMH reusable principle:** Editability ≠ correctness; central storage ≠ governance; publication requires validated, versioned, traceable evidence.
