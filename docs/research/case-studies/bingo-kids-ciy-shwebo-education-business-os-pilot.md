# Bingo-Kids Learning Centre × CIY.Club — Shwebo Education Business OS Pilot

**Status:** Discovery / design candidate. No partner authorization, live integration, or production execution is claimed.

## Case summary

The supplied case material describes Bingo-Kids Learning Centre in Shwebo and its founder/teacher Shwe Yi Lin discussing CIY.Club's open-ended creative technology learning approach. The posts emphasize child-led creation, experimentation, creative thinking, discussion, problem-solving, and student work. They mention improvement after two months, but include no baseline dataset, rubric scores, or independently verified outcomes.

### Supplied details requiring confirmation

- Centre: Bingo-Kids Learning Centre, Shwebo
- CIY campus address supplied: Lane (4), beside Industrial Zone main road, Taung Myo Taung, Ward (10), Shwebo
- CIY campus phone supplied: 09 972767489
- Bingo-Kids phone supplied: 09 964446788

A third-party directory lists Bingo-Kids with a different Shwebo address variant. Confirm the operating relationship and physical address directly before using these details operationally.

## External references

- CIY Club Myanmar official site: https://www.ciyclub.com.mm/en
- CIY.Club global site: https://www.ciy.club/
- Third-party Bingo-Kids listing (not authoritative): https://www.schoolandcollegelistings.com/MM/Shwebo/163971934174312/Bingo-Kids-Learning-Centre

The Myanmar CIY site describes a consumer-to-creator approach for ages 7–17, hands-on projects and coaching. Its displayed network metrics are website claims and have not been independently audited in this case study.

## Opportunity

Create a visible and trustworthy learner-development journey, not merely a course-enrolment database:

`Enquiry → Registration → Course/Batch → Attendance → Learning Activity → Student Project → Assessment → Teacher Review → Parent Report → Renewal`

A student portfolio with dated artifacts and teacher feedback can substantiate parent communication. Avoid unsupported claims about learning gains.

## MVP scope

1. **Student & Guardian:** minimal profiles, authorized guardian relationship and consent.
2. **Course & Batch:** pathway, coach, schedule, capacity and enrollment.
3. **Attendance:** dated session record and absence follow-up.
4. **Learning Progress:** observable skill rubric, milestone and teacher note.
5. **Project Portfolio:** title, description, artifact reference, version and visibility approval.
6. **Parent Report:** generated from approved records; teacher approval required before publication.
7. **Payments:** invoice, payment status, balance and receipt reference.
8. **Operations Dashboard:** enrollment, attendance, retention, project completion and collections.

## Suggested measurement protocol

Capture a baseline in week 1 and repeat the same rubric in week 8. Use defined 1–4 descriptors for:
- originality and idea explanation;
- ability to debug and explain a solution;
- task completion with independence/support level;
- project completion and iteration;
- ability to present work and reflect on feedback;
- attendance and participation.

No comparative ranking of children. Do not report improvement until the baseline and follow-up records exist.

## Proposed Firebase architecture

- Firebase Authentication for staff and guardian sign-in.
- Cloud Firestore for structured operational records.
- Cloud Storage for approved project artifacts.
- Cloud Functions for trusted server-side workflows and report generation.
- Separate development, staging and production environments.
- Role-based access: centre owner/admin, teacher/coach, guardian, and student where needed.

Suggested collections:
`centres`, `users`, `students`, `guardians`, `courses`, `batches`, `enrollments`, `sessions`, `attendance`, `assessments`, `projects`, `projectArtifacts`, `parentReports`, `invoices`, `payments`, `auditEvents`.

Every query and write must be centre-scoped and authorized. Never trust client-supplied role claims or centre IDs without server-side/rules validation.

## Child privacy and security gates

- Obtain operator authorization and parent/guardian consent before collecting real child data.
- Collect only information needed to deliver the learning service.
- Keep portfolios private by default; public sharing requires separate explicit authorization.
- Separate internal teacher notes from parent-visible content.
- Use authenticated, expiring artifact access rather than public file URLs.
- Establish retention, correction, export and deletion procedures.
- Define moderation and safeguarding controls for any showcase/community feature.
- Verify applicable local legal requirements and cross-border transfer conditions before production.

## Delivery gates and evidence

| Gate | Deliverable | Required evidence |
|---|---|---|
| G0 Discovery | Confirm operator, partnership, scope and consent | Written pilot approval and verified site details |
| G1 Foundation | Firebase environments, identity and role model | Deployed config, rules tests, access matrix |
| G2 Core records | Student, guardian, course, batch, enrollment | CRUD tests and negative authorization tests |
| G3 Learning workflow | Attendance, rubric, portfolio | Synthetic learner end-to-end test |
| G4 Parent reporting | Teacher-approved report | Approval log and guardian-access test |
| G5 Operations | Payments and KPI dashboard | Reconciled synthetic records |
| G6 Acceptance | UAT and security review | Defect register, UAT sign-off |
| G7 Release | Controlled production deployment | Release identifier, monitoring and restore evidence |

## Immediate next actions

- [ ] Confirm whether Bingo-Kids and CIY Shwebo are the same operator, a franchise/partner campus, or separate entities.
- [ ] Verify address, contact, age bands, course catalog, schedules, class size and pricing.
- [ ] Obtain written permission for a pilot and agree data controller/operator responsibilities.
- [ ] Prototype with synthetic learners only.
- [ ] Validate Firestore security rules and guardian access before any real child record is entered.
- [ ] Run acceptance tests and obtain sign-off before production.

## Evidence boundary

This document records supplied case-study statements and a proposed technical design. The repository does not yet contain a Firebase integration for this pilot. No live centre integration, real student data processing, deployed application, or production outcome is asserted.
