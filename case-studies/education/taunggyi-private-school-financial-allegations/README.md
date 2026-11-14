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


## Research continuation — Phase 41 (2026-11-13)

**Status:** New secondary-source follow-up found. No primary financial, police or court evidence added.

### 1. Follow-up report — The People Voice, 2026-11-12

Source: https://mm.thepeoplevoicepaoh.com/news/20118/

The article attributes the following claims to affected people:

| Reported claim | Amount / detail | Classification |
|---|---:|---|
| Outside shareholder contribution | MMK 1,250 lakhs | Media-reported allegation |
| Parent/shareholder contribution | MMK 850 lakhs | Media-reported allegation |
| Another parent contribution | MMK 500 lakhs | Media-reported allegation |
| Education employee's acquaintance / parent contact | MMK 650 lakhs | Media-reported allegation |
| Arithmetic subtotal of the four claims | MMK 3,250 lakhs (MMK 325,000,000) | Arithmetic only; not verified loss |
| Share contribution offer to another parent | MMK 300 lakhs; reportedly declined | Reported solicitation, not a loss |
| Teacher-salary funding request | MMK 30 lakhs reportedly requested from a parent before Thadingyut | Reported request; disbursement not established |
| Principal's reported position | Academic work might continue; financial matters would not be taken on | Second-hand report, not a formal undertaking |

The MMK 3,250-lakh figure is only the arithmetic sum of four claims quoted by the article. It is not an audited total, not necessarily exhaustive, and may not equal outstanding loss. No original agreements, bank transfers, receipts, repayment records or claimant-level duplicate checks were available.

**Source-dependence limitation:** the four amounts exactly repeat the amounts in the Democratic Press article supplied in the conversation. The People Voice follow-up is a second publication event, but the matching figures must not be counted as two independent confirmations because the reports may rely on overlapping claimants or the same underlying source network. Preserve two publication records and a possibly shared claim/source cluster until separate first-hand claimant evidence is obtained.

The article also says the school began operating in 2026 and had not yet reached one year; the exact opening date remains unverified.

### 2. Distinguish separate salary/collateral allegations

The Democratic Press report supplied in the conversation (2026-11-10) described a teacher who allegedly lent MMK 2 lakhs and a separate gold-necklace collateral dispute. The People Voice follow-up (2026-11-12) separately describes a request to borrow MMK 30 lakhs from a parent for teacher salaries.

Do not merge these into one transaction or treat them as a contradiction without claimant identity, dates and original records. Record separate claim IDs and distinguish requested, agreed, disbursed, collateral pledged, repaid and outstanding amounts. The gold-necklace claim remains unverified.

### 3. Related entity — Maths World Olympiad Centre

The People Voice report also says the founder operated a Maths World International Olympiad Mathematics Centre and reports that it is currently closed.

A third-party directory reproducing older public-facing posts contains:
- 2026-09-14: award/certificate collection notice showing No. 146, Khwa Nyo Street, Pyidawthar Ward, Taunggyi.
- 2026-07-19: second-campus opening notice for Room 2, Building 11, Shwe Taung Kyar Lane 5, Shan Kwin Ward, Taunggyi; classes were stated to begin 2026-08-08.

Source: https://www.schoolandcollegelistings.com/MM/Taunggyi/140372492486398/Maths-World-Olympiad-Centre

This is an archived third-party snapshot of public posts, not an MOE authorization or current-operating-status record. The school registry address (ပ/၃၁၀၊ နီလာလမ်း) differs from the centre's listed addresses. Keep separate institution and campus records and record only a source-linked, unverified reported association. Do not infer a common licence or legal ownership.

### 4. Regulatory source correction — international-curriculum directive

MOE's guideline page lists Notification 18/2023, Notification 16/2023, registration-form distribution, Notifications 1/2024 and 2/2024, and a separate International School instructions link:
- https://moe.gov.mm/my/node/5310
- https://www.moe.gov.mm/my/node/4536

DFDL reports three directives issued on 2023-11-07 for higher education, national-curriculum basic schools and international-curriculum schools:
- https://www.dfdl.com/insights/legal-and-tax-updates/myanmar-new-directives-on-registration-of-private-educational-institutions/

The MOE's own directives page lists three separate instruction titles, including the instruction for private schools teaching the international curriculum:
- MOE Supervisory Board directives: https://moe.gov.mm/my/node/4526
- MOE International School instructions: https://www.moe.gov.mm/my/node/4536

DFDL reports that three directives were issued on 2023-11-07 for higher education, national-curriculum basic schools and international-curriculum schools:
- https://www.dfdl.com/insights/legal-and-tax-updates/myanmar-new-directives-on-registration-of-private-educational-institutions/

**Important source conflict:** the VDB-Loi November 2023 digest lists Directives 16/2023, 17/2023 and 18/2023, but its narrative sequence (higher education, national-curriculum basic schools, international-curriculum schools) conflicts with the primary MOE PDFs: Notification 16/2023 is higher education, while Notification 18/2023 is national-curriculum basic education. Do not use the VDB sequence to override the signed MOE instruments. A 2025 Myanmar Academy of Arts and Science journal bibliography identifies Notification 17/2023 as the international-curriculum directive, which is consistent with the MOE PDFs and separate MOE International School instructions page:
- https://maas.edu.mm/Research/Admin/pdf/26.%20Dr.Thida%20Tun%20%28347-356%29.pdf

**Updated classification:** the existence and category of a separate international-curriculum instruction are confirmed by MOE; mapping it to No. 17/2023 is **Supported — primary instrument pending** because the signed MOE instrument bearing No. 17/2023 was not retrieved in this pass. Notification 18/2023 remains directly verified as the national-curriculum basic education directive.

### 5. Claim-level evidence matrix update

| Item | Classification | Required evidence |
|---|---|---|
| Four amounts in People Voice report | Supported as published claimant allegations | Claimant-authorized agreements, transfers, receipts and repayments |
| MMK 3,250-lakh subtotal | Arithmetic over four reported claims only | Reconciled ledger; never call verified total loss |
| MMK 300-lakh share offer reportedly declined | Reported solicitation; not a loss | Original message/call record or claimant statement |
| MMK 30-lakh salary-funding request | Reported request; payment not established | Evidence showing whether funds were disbursed |
| MMK 2-lakh loan and gold collateral | Supplied media allegation; unverified | Separate claimant statement and transaction/collateral evidence |
| Principal's reported position | Second-hand report | Direct written statement or authorized meeting record |
| Maths World Centre and old addresses | Archived third-party public-post snapshot | Official entity/authorization and campus records |
| Maths World Centre closure | Media-reported | On-site or competent-authority confirmation |
| Police complaint / arrest / court outcome | Unknown | Official police or court reference |

### 6. Proposed KMH NEXUS V41 design — not implemented

Add a **Related Institution & Campus Registry** and a **Claim Lifecycle Ledger**.

Suggested related-entity design:
- Institution: Htoo Yadanar Aung private basic school.
- Related institution: Maths World Olympiad Centre.
- Relationship assertion: reported founder/operator association; not verified legal ownership.
- Campus: one row per address, with valid-from, valid-to, source and status.
- Never infer common licence, legal entity or ownership from similar branding, a media article or a shared named founder.

Suggested claim lifecycle:
- Solicited → Agreed → Disbursed → Partially Repaid / Repaid → Disputed / Reviewed.
- Collateral: Offered → Pledged → Released / Disputed.

Only evidence-backed disbursements enter the cash-loss ledger. Declined offers and unfulfilled requests are excluded from financial-loss calculations.

### 7. New QA acceptance tests

- [ ] Four reported claims remain separate, source-linked records.
- [ ] MMK 3,250 lakhs is labelled an unverified reported subtotal, not total loss.
- [ ] Declined MMK 300-lakh offer is excluded from loss calculations.
- [ ] MMK 30-lakh request is not treated as disbursed without proof.
- [ ] MMK 2-lakh loan and gold collateral are separate events.
- [ ] School and Olympiad centre have separate institution/campus records.
- [ ] Archived campus posts do not establish current status or licence.
- [ ] Reported founder association is not converted into verified legal ownership.
- [ ] Notification 17/2023 remains Supported / primary instrument pending.
- [ ] Police and court status remain Unknown absent official references.

### 8. Implementation gate

This phase adds research and schema design only. No case-specific database, API, claim ingestion, financial reconciliation, campus verification or runtime QA has been executed. Case-module implementation remains **NOT STARTED / NOT VERIFIED**.

Next action: preserve the two follow-up articles and the archived Maths World listing with retrieval dates and hashes; collect claimant-authorized evidence under pseudonymous IDs; then implement the claim lifecycle ledger in a reviewed branch.
