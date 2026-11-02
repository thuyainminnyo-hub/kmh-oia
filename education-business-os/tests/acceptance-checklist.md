# Pilot acceptance checklist

## Database
- [ ] Course and batch documents use stable IDs and validated fields.
- [ ] MMK amounts are positive integers; no floating-point currency.
- [ ] Duplicate student records are reviewed before merging.

## Authentication and authorization
- [ ] Every organization-owned document stores a validated `organizationId`.
- [ ] Active organization membership is required for tenant-scoped callable operations.
- [ ] Organization roles are read from `organizations/{organizationId}/members/{uid}`, not trusted from client-supplied data.
- [ ] Organization A cannot read or mutate Organization B's courses, batches, enrollments, payments or learning records.
- [ ] Unscoped collection queries that could cross organization boundaries are denied.
- [ ] Platform admin bootstrap is protected by a server-managed `platformAdmin` custom claim.
- [ ] Unauthenticated reads and writes are denied.
- [ ] Student reads only own records.
- [ ] Instructor reads only assigned batch records (assignment constraints must be completed before production).
- [ ] Only admin manages courses/batches and verifies payments.
- [ ] Client cannot assign or change custom role claims.

## Multi-organization
- [ ] Platform admin can bootstrap an organization and its first admin membership.
- [ ] Organization admin can provision and suspend members using an audited callable function.
- [ ] Last active organization admin cannot be suspended or demoted until another active admin exists.
- [ ] Enrollment assignment accepts only an active instructor membership from the same organization.
- [ ] A user with active membership in one organization cannot use its role in another organization.
- [ ] Suspended membership loses organization access.
- [ ] Organization identifiers are validated as safe single document IDs.
- [ ] Same-school student ownership and instructor assignment restrictions remain enforced.

## Workflows
- [ ] Paid enrollment begins in pending_payment; free enrollment may activate immediately.
- [ ] Payment submissions reserve the remaining balance and cannot exceed the fee.
- [ ] Partial verified payments reduce the balance but do not activate enrollment.
- [ ] Full verified payment activates enrollment atomically with the payment update.
- [ ] Rejected payment releases its reserved amount without increasing paidAmount.
- [ ] Duplicate verification is denied and does not double-count funds.
- [ ] Enrollment and payment transitions are audited.
- [ ] Payment enters pending; admin reconciliation verifies/rejects.
- [ ] Attendance supports present/absent/late/excused for sessions 1–24.
- [ ] Assessment score is constrained to 0–100.
- [ ] Completion outcome links to evidence.

## Release evidence
- [ ] Firebase Emulator Suite rules tests pass.
- [ ] Functions build and payment state unit tests pass.
- [ ] Functions Emulator integration tests cover enrollment/payment transactions.
- [ ] Web production build passes.
- [ ] Mobile debug build passes.
- [ ] Rules and indexes deployed to the intended Firebase project.
- [ ] Smoke tests use synthetic accounts.
- [ ] Commit, test output, emulator logs and approver are recorded.
