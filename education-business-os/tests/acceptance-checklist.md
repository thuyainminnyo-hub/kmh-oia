# Pilot acceptance checklist

## Database
- [ ] Course and batch documents use stable IDs and validated fields.
- [ ] MMK amounts are positive integers; no floating-point currency.
- [ ] Duplicate student records are reviewed before merging.

## Authentication and authorization
- [ ] Unauthenticated reads and writes are denied.
- [ ] Student reads only own records.
- [ ] Instructor reads only assigned batch records (assignment constraints must be completed before production).
- [ ] Only admin manages courses/batches and verifies payments.
- [ ] Client cannot assign or change custom role claims.

## Workflows
- [ ] Enrollment is created and status changes are audited.
- [ ] Payment enters pending; admin reconciliation verifies/rejects.
- [ ] Attendance supports present/absent/late/excused for sessions 1–24.
- [ ] Assessment score is constrained to 0–100.
- [ ] Completion outcome links to evidence.

## Release evidence
- [ ] Firebase Emulator Suite rules tests pass.
- [ ] Functions build and tests pass.
- [ ] Web production build passes.
- [ ] Mobile debug build passes.
- [ ] Rules and indexes deployed to the intended Firebase project.
- [ ] Smoke tests use synthetic accounts.
- [ ] Commit, test output, emulator logs and approver are recorded.
