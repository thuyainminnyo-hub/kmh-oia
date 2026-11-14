# EDU INTEGRITY NEXUS — Project Charter & Architecture

**Approved project name:** EDU INTEGRITY NEXUS  
**Short name:** EIN  
**Parent architecture:** KMH NEXUS  
**Approval date:** 2026-11-14  
**Decision scope:** Internal project naming decision only. Not trademark clearance, registration, company-name clearance, domain availability confirmation or legal approval.

## 1. Project identity

**Full name:** EDU INTEGRITY NEXUS  
**Expansion:** Education Integrity & Accountability Nexus  
**Category:** Evidence-based education institutional integrity, governance and accountability intelligence initiative  
**Tagline:** Evidence Before Conclusion. Integrity Through Verification. Accountability Through Governance.

EDU INTEGRITY NEXUS is a KMH NEXUS initiative designed to organize and verify education-institution identity, authorization, regulatory obligations, financial claims, stakeholder protection, case evidence and institutional accountability. It is an evidence-management and decision-support system, not a court, regulator, police authority, credit bureau or public accusation platform.

## 2. Naming hierarchy

- Parent architecture: KMH NEXUS
- Initiative: EDU INTEGRITY NEXUS
- Short identifier: EIN
- Pilot case: HRA-TGG-2026-001 — Taunggyi Private School Financial Allegations & Institutional Accountability
- Pilot workstream: Financial Evidence Engine
- Research records: Notion case archive and GitHub case-study Markdown file

Do not rename KMH NEXUS. EDU INTEGRITY NEXUS is a governed child initiative.

## 3. Mission and principles

Mission: enable evidence-led, privacy-protective and independently reviewable accountability processes for education institutions and stakeholders.

1. Evidence before conclusion.
2. Allegation is not a finding of fact or guilt.
3. Every material claim has provenance, source quality, date and review status.
4. Distinguish institution, legal entity, campus, brand, operator and authorization.
5. Distinguish requested, agreed, disbursed, repaid, disputed and outstanding amounts.
6. Protect students, parents, teachers, claimants and whistleblowers through minimization and access control.
7. Keep unknown distinct from false, negative or not applicable.
8. Human review is mandatory for high-impact decisions.
9. No automated guilt scoring, public blacklisting, licence revocation, closure, debt collection or legal adjudication.
10. Implementation status is evidence-gated; architecture or CI success does not prove production readiness.

## 4. Scope

### In scope
- Institution, legal-entity, campus, programme and authorization registries.
- Regulatory source library with jurisdiction, instrument type, effective dates, version and applicability review.
- Evidence/source registry with original files/URLs, timestamps, hashes, custody, provenance and access classes.
- Stakeholder claim intake using pseudonymous identifiers and consent.
- Claim lifecycle and financial transaction reconciliation.
- Payroll, collateral and repayment evidence records.
- Student continuity and record-transfer coordination.
- Case management, conflicts, review decisions, audit events and reporting.
- Role-based access, retention, privacy and independent QA.

### Out of scope
- Declaring any person guilty or fraudulent.
- Publishing personal data or unverified accusations.
- Replacing police, courts, education authorities, auditors or legal counsel.
- Automated creditworthiness, fraud-propensity or individual risk scoring.
- Seizing assets, collecting debts, revoking licences or closing schools.
- Treating media repetition as independent corroboration.
- Inferring licensing from a registry row or directory listing alone.

## 5. Reference architecture

1. **Institution & Authorization Registry** — distinct records for institution, legal entity, operator, campus, programme, certificate and source.
2. **Regulatory Intelligence Library** — primary instruments first; applicability, version, effective date, amendments and jurisdiction.
3. **Source & Evidence Registry** — original files/URLs, timestamps, cryptographic hashes, custody, provenance, reliability and access controls.
4. **Stakeholder & Consent Layer** — pseudonymous claimant/guardian/staff identities, lawful purpose, consent and restricted identity vault.
5. **Claim Lifecycle Engine** — SOLICITED → AGREED → DISBURSED → PARTIALLY_REPAID / REPAID → DISPUTED / REVIEWED.
6. **Financial Reconciliation Engine** — transaction-level inflows/outflows, repayment, duplicate detection, currency/unit normalization and balance calculations.
7. **Student Continuity Module** — records, examinations, transfer requests and guardian-authorized continuity support.
8. **Case Management & Review** — issues, evidence links, contradictions, reviewer findings and human decisions.
9. **Governance & Audit Layer** — RBAC, separation of duties, append-only audit events, retention, incident response and approvals.
10. **Reporting & Decision Support** — evidence-qualified summaries with explicit confidence and limitations; no guilt labels or automated enforcement.

## 6. Core data domains

- institution_registry
- legal_entities
- operator_relationships
- campuses
- programmes
- authorization_records
- regulatory_instruments
- regulatory_applicability_reviews
- source_registry
- evidence_registry
- evidence_custody_events
- stakeholder_identity_vault
- consent_records
- claims
- claim_source_links
- transactions
- repayments
- collateral_events
- payroll_claims
- student_continuity_cases
- case_events
- review_decisions
- conflicts_and_disputes
- audit_events
- access_events
- retention_and_deletion_requests

Every record should carry a stable ID, timestamps, source links where applicable, status, reviewer and version history. Identity data must be segregated from case evidence and accessible only to authorized roles.

## 7. Evidence status taxonomy

- CONFIRMED — authoritative primary evidence supports the exact fact within scope and date.
- SUPPORTED — credible secondary evidence; independent primary confirmation remains.
- UNVERIFIED — insufficient evidence or not independently checked.
- DISPUTED — material sources conflict.
- UNKNOWN — no reliable information located.
- NOT_ASSESSED — outside the current review.

Source publication, claim existence, transaction existence, outstanding balance and legal finding are separate propositions. A source can confirm that a statement was published without confirming the truth of the statement.

## 8. Governance and security gates

- Least-privilege role-based access and separation of duties.
- Pseudonymization by default; identity re-linking requires explicit authorized purpose.
- Encryption in transit and at rest; secrets managed outside source control.
- Evidence hashes and append-only custody/audit events.
- Consent, lawful basis, retention and deletion workflow.
- Human approval before external disclosure, legal-status changes or high-impact recommendations.
- Independent QA for arithmetic, source dependence, duplicate claims, conflicts and privacy.
- No production deployment without security review, threat model, backup/restore evidence, monitoring and rollback plan.

## 9. Pilot: Taunggyi education case

Pilot ID: HRA-TGG-2026-001.

The pilot uses the existing case archive. Its current record separates MOE registry facts from media-reported allegations and unknown police/court status. Reported amounts are not treated as verified loss. Matching figures across publications are not independent corroboration unless source independence is established. The school and Maths World Olympiad Centre are separate institution/campus records unless primary records prove their legal relationship.

The pilot is research/design only. No case-specific database, API, financial reconstruction, claimant intake, runtime QA or production deployment is currently evidenced.

Existing records:
- Notion case archive: https://app.notion.com/p/415fd51bf575810ebf4edc4a1803f5ff
- GitHub repository: https://github.com/thuyainminnyo-hub/kmh-oia
- Case-study file: https://github.com/thuyainminnyo-hub/kmh-oia/blob/docs/case-study-taunggyi-school-accountability/case-studies/education/taunggyi-private-school-financial-allegations/README.md
- Existing case documentation PR #228: https://github.com/thuyainminnyo-hub/kmh-oia/pull/228 (Draft / unmerged; separate from this new project charter).

## 10. Phased roadmap and acceptance gates

### Phase 0 — Project identity and charter
- [x] Project name approved.
- [x] Parent-child naming hierarchy defined.
- [x] Mission, scope, exclusions and principles documented.
- [ ] Charter reviewed and accepted in GitHub.

### Phase 1 — Source and evidence foundation
- [ ] Source/evidence schema and provenance model.
- [ ] SHA-256 manifest and evidence custody.
- [ ] Source-dependence and duplicate-source handling.
- [ ] Evidence classification and reviewer workflow.

### Phase 2 — Institution and regulatory registry
- [ ] Separate legal entity, institution, operator, campus and programme.
- [ ] Authorization records with exact certificate IDs and validity dates.
- [ ] Regulatory instrument versioning and applicability review.

### Phase 3 — Claim and transaction ledger
- [ ] Pseudonymous claim intake and consent.
- [ ] Claim lifecycle state machine.
- [ ] Transaction/repayment/collateral records.
- [ ] Duplicate detection and reconciled balances.

### Phase 4 — Stakeholder protection and student continuity
- [ ] Student records and transfer workflows.
- [ ] Staff payroll claims.
- [ ] Guardian/claimant privacy and access boundaries.

### Phase 5 — Case management, QA and governance
- [ ] Conflict/contradiction management.
- [ ] Independent reviewer workflow.
- [ ] Tamper-evident audit and access events.
- [ ] Disclosure approval and retention/deletion controls.

### Phase 6 — Pilot execution and production gate
- [ ] Synthetic-data tests first.
- [ ] Authorized, consented evidence intake only.
- [ ] Case-specific integration and security tests.
- [ ] Independent QA sign-off.
- [ ] Human approval for production deployment.
- [ ] Monitoring, backup/restore and rollback evidence.

## 11. Implementation truth

Current status: **CHARTER DRAFTED — IMPLEMENTATION NOT STARTED / NOT VERIFIED.**

This is documentation. It does not prove code, database, APIs, data ingestion, deployment, legal compliance or operational readiness. Existing repository CI success on a separate documentation PR is not evidence that EDU INTEGRITY NEXUS has been implemented.

## 12. Naming and intellectual-property note

The project owner approved EDU INTEGRITY NEXUS as an internal project name on 2026-11-14. This approval is not trademark clearance, registration, company-name clearance, domain availability confirmation or legal advice. Before public/commercial launch, search relevant trademark registers in intended markets, company registries, domain registries and similar software/services. Record search scope, classes, jurisdictions, dates and results; obtain qualified legal review before adoption as a public brand.

## 13. Naming research references

- Institute for Research Software, Choosing Project and Product Names: https://www.software.ac.uk/guide/choosing-project-and-product-names
- Apache Software Foundation, New Project and Software Product Naming Process: https://apache.org/foundation/marks/naming.html
- WIPO, Making a Mark: https://www.wipo.int/edocs/pubdocs/en/wipo-pub-900-1-en-making-a-mark-an-introduction-to-trademarks-for-small-and-medium-sized-enterprises.pdf
- MyIPO, Chapter 5 — Distinctiveness: https://www.myipo.gov.my/wp-content/uploads/2026/03/Chapter-5-Distinctiveness.pdf

A preliminary web search also surfaced a US registration for the separate mark “NEXUS UNIVERSITY” in education services. This is not a determination about EDU INTEGRITY NEXUS; it reinforces the need for a jurisdiction- and class-specific search before external launch.
