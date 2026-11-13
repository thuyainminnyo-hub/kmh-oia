# Case Study — Taunggyi Private School Financial Allegations & Institutional Accountability

**Research record:** 2026-11-11  
**Working ID:** HRA-TGG-2026-001 (internal research identifier; not an official police/court case number)  
**Status:** Research synthesis and design record. No independent financial reconstruction or production implementation is claimed.

## 1. Research question

How can a school's public registration identity, applicable education regulations, reported financial claims, staff/parent claims, and student-continuity risks be recorded and independently verified without converting media allegations into findings of guilt?

## 2. Evidence classification

- **Confirmed:** directly supported by an identified authoritative primary source, within its stated scope and date.
- **Supported:** credible secondary-source reporting, but independent confirmation remains.
- **Unverified:** insufficient evidence or not independently checked.
- **Disputed:** material sources or claims conflict.
- **Unknown:** no reliable information located.
- **Not assessed:** outside this research pass.

A media report establishes that a report was published; it does not itself prove the allegations. A registry entry does not establish current operational status, current licence validity, financial integrity, or criminal liability.

## 3. Institution identity — MOE registry record

MOE's 2026–2027 private basic education school list contains:

| Field | Record |
|---|---|
| List serial | 1416 |
| School name | ထူးရတနာအောင် |
| State | Southern Shan State |
| Township | Taunggyi |
| Listed level | Primary |
| Listed grades | KG–G5 |
| Listed address | ပ/၃၁၀၊ နီလာလမ်း၊ ပြည်တော်သာရပ်၊ တောင်ကြီး |

Source: https://moe.gov.mm/my/node/5520/

**Limit:** 1416 is the list serial, not a verified licence number. The dated list entry does not independently establish the school's status on 2026-11-11, the expiry date of any certificate, or whether a separate centre/programme had a distinct authorization.

## 4. Reported allegations — secondary sources

Sources:
- Democratic Press report dated 2026-11-10 (article text supplied in the conversation).
- Myanmar Pressphoto Agency report: https://mpanews.info/headline/14457/

The articles report allegations involving investment/share contributions, loans, staff salary claims, a gold-collateral dispute, and the reported departure/closure of the school operation.

Individual sums, the claimed aggregate loss exceeding MMK 10,000 lakhs, claimant count, collateral details, earlier Minbu allegations and total outstanding liabilities have not been independently reconciled against original contracts, bank statements, receipts, payroll evidence, or claimant-authorized statements.

Police complaint, FIR/case number, arrest, charge, court judgment, asset seizure, and recovery remain **Unknown** in this research record. Unknown does not mean that no such event exists.

## 5. Regulatory source map

### Notification 18/2023

Official MOE PDF: https://www.moe.gov.mm/sites/default/files/announcement/2024/18_2023.pdf

This is the primary starting point for national-curriculum private basic education schools. Provisions reviewed in this research concern application evidence, financial and operational records, classroom requirements, teachers, student records, branch applications and temporary registration.

Exact wording, later amendments, effective dates, and applicability must be rechecked against the full official instrument before any compliance finding.

### Other education instruments

MOE guidelines hub: https://moe.gov.mm/my/node/5310

Notification 16/2023 concerns private higher education and should not automatically be applied to a basic education school. The exact number and legal status of an international-curriculum directive discussed in earlier research remain to be confirmed from its original published instrument. Do not assert Notification 17/2023 without primary-source confirmation.

### 2027–2028 standards and Directive 44

MOE page: https://moe.gov.mm/my/node/5310  
Media report: https://elevenmyanmar.com/news/44-directives-issued-for-private-schools-including-ban-on-opening-in-apartment-buildings-and?language=my

The existence of an MOE page about 2027–2028 new-school standards is a primary-source page fact. Detailed requirements attributed to Directive 44 remain secondary-source reporting until the original directive, annexes, effective date, transitional provisions and scope are obtained and reviewed.

### Temporary permits

GNLM report: https://www.gnlm.com.mm/only-qualified-educational-institutions-will-be-allowed-to-register-next-year/

The report describes 1,092 temporary-permit schools and a one-year preparation programme. This is distinct from the separate two-year temporary-certificate provision described in Notification 18/2023 Clause 11. Neither status is attributed to this school without its actual certificate.

## 6. Evidence matrix

| Item | Status | Next evidence required |
|---|---|---|
| MOE list entry | Confirmed, limited to list entry | Preserve dated source and exact row |
| List serial 1416 | Confirmed | Never label as licence number |
| Listed KG–G5 scope | Confirmed as listed | Current certificate and amendments |
| Founder identity | Media-reported | Official registration/authorized evidence |
| Investment/share fraud | Allegation | Agreements, bank transfers, receipts, legal review |
| Individual loss amounts | Unverified | Claimant-level evidence and duplicate checks |
| Aggregate loss | Unverified | Reconciled claim ledger and repayments |
| Staff salary arrears | Unverified | Employment terms, attendance, payroll and bank records |
| Gold collateral claim | Unverified | Ownership, pawn/loan and return/payment evidence |
| Departure/closure | Media-reported | Authority or on-site confirmation |
| Police complaint/investigation | Unknown | Official police acknowledgment/reference |
| Arrest/charge | Unknown | Official police/prosecutor/court record |
| Court judgment | Unknown | Official/certified court record |
| Asset recovery | Unknown | Enforcement/recovery records |

## 7. Investigation workflow

1. Preserve MOE registry, legal documents and media articles with publication/retrieval dates, URLs and SHA-256 hashes.
2. Separate institution name, list serial, actual certificate number, founder/operator, campus, approved grades, and any separate centre/branch.
3. Obtain authorized licence, renewal, branch and closure records through the competent authority.
4. Collect claims with informed consent and pseudonymous claimant IDs. Do not publish names, contact details, bank accounts, signatures, student identities, or home addresses.
5. Reconstruct each inflow, outflow and repayment from source-backed transactions. Separate principal, interest, promised returns, collateral and disputed amounts; detect duplicate transfers and duplicate reporting.
6. Reconcile payroll using employment terms, attendance, payroll ledger, bank payment and acknowledgement.
7. Handle student records, examinations, transfers and academic continuity separately from financial claims.
8. Update police/court status only from official references.
9. Require independent QA for source quality, arithmetic, duplicates, conflicts, privacy and conclusions.
10. Refer potential wrongdoing to competent authorities; the system does not decide guilt, close schools, revoke licences or adjudicate claims.

## 8. Proposed KMH NEXUS data model — design only

Suggested entities:
- `source_registry`: publisher, source type, URL, publication/retrieval dates, hash and verification status.
- `institution_registry`: institution identity, list serial, township, address, school type and source.
- `authorization_records`: actual certificate number, authority, issue/expiry dates, approved grades, campus and evidence.
- `claims`: pseudonymous claimant ID, claim type, claimed amount/currency, status, source and consent reference.
- `transactions`: date, direction, amount, currency, evidence, duplicate group and reconciliation status.
- `repayments`: amount, date and evidence.
- `staff_payroll_claims`: pseudonymous staff ID, period, agreed/paid amount and evidence.
- `student_continuity_cases`: pseudonymous student ID, record transfer, examination status and guardian consent.
- `legal_status_events`: authority, event type, official reference, date and source.
- `evidence_registry`: custodian, received time, hash, access class, chain of custody and source.
- `review_decisions` and `audit_events`: reviewer, rationale, linked evidence, actor and tamper-evident event history.

Privacy controls: data minimization, access tiers, encryption, retention controls, consent tracking and no public disclosure of claimant/student personal information.

## 9. QA acceptance criteria

- [ ] List serial cannot be stored as licence number.
- [ ] Every rule has jurisdiction, institution type, source, effective date and version.
- [ ] Media allegations cannot auto-promote to legal findings.
- [ ] Unknown is distinct from false/no event.
- [ ] Each claim and transaction links to separate evidence.
- [ ] Duplicate claim/payment detection is tested.
- [ ] Repayment balances reconcile with auditable arithmetic.
- [ ] Claimant/student fields are pseudonymized and access-controlled.
- [ ] Police/court status requires official reference.
- [ ] Human review and independent QA are logged.
- [ ] Actual database/API execution and test output exist before marking implementation PASS.

## 10. Implementation status

This is a research/design record only. No PostgreSQL schema, API, transaction reconstruction, deployment or QA run for this specific case is evidenced. The existence of the KMH OIA repository does not prove this case module has been implemented.

**Gate:** Research synthesis saved; implementation remains NOT STARTED / NOT VERIFIED.

## 11. Sources

- MOE 2026–2027 school list: https://moe.gov.mm/my/node/5520/
- MOE Notification 18/2023 PDF: https://www.moe.gov.mm/sites/default/files/announcement/2024/18_2023.pdf
- MOE guidelines hub: https://moe.gov.mm/my/node/5310
- MOE Supervisory Board responsibilities: https://moe.gov.mm/en/content/responsibilities-private-school-supervisory-board
- MPA report, 2026-11-10: https://mpanews.info/headline/14457/
- Democratic Press report, 2026-11-10 (text supplied in conversation; retain as a separate media-source record).
- Eleven Media report on Directive 44: https://elevenmyanmar.com/news/44-directives-issued-for-private-schools-including-ban-on-opening-in-apartment-buildings-and?language=my
- GNLM temporary-permit report: https://www.gnlm.com.mm/only-qualified-educational-institutions-will-be-allowed-to-register-next-year/

## 12. Next action

Capture a source snapshot bundle first, then implement the source/evidence registry and claim/transaction ledger in a separate reviewed branch. Do not import claimant personal data or assert guilt.
