# Education Business OS — Aptivern Flutter Foundation Batch 5

Firebase-backed Web + Flutter pilot for course registry, enrollment, payment, attendance, assessment and student outcomes.

## Pilot configuration
- Pilot ID: APT-FLUTTER-B5
- Course: Flutter Foundation, Batch 5
- Start: 2026-11-07
- Schedule: Saturday/Sunday, 14:00–16:00 (timezone must be confirmed)
- Duration: 12 weeks, 24 sessions, 48 hours
- Listed fee: 300,000 MMK
- Final project: Weather App

These values come from the supplied case study. They are configuration, not proof of enrollment, payment or delivery. No real student data is seeded.

## Architecture
- Web: React + TypeScript + Vite
- Mobile: Flutter client starter
- Backend: Firebase Auth, Cloud Firestore, Cloud Functions
- Tenancy: organization-scoped records with `organizationId`
- Membership: `organizations/{organizationId}/members/{uid}`
- User workspace index: `userOrganizationMemberships/{uid}/organizations/{organizationId}`
- Authorization: active organization membership and server-managed `platformAdmin` custom claim for platform bootstrap
- Audit: append-only server-created organization-scoped audit records
- OIA: event integration contract; no live OIA connection is claimed.

## Main collections
- Tenant data: `organizations`, `courses`, `batches`, `enrollments`, `payments`, `attendance`, `assessments`, `outcomes`, `auditLogs`.
- Membership: `organizations/{organizationId}/members/{uid}`.
- User membership directory: `userOrganizationMemberships/{uid}/organizations/{organizationId}`.

Every tenant-owned course, batch, enrollment, payment, attendance, assessment, outcome and audit record must carry the correct `organizationId`. Client queries must include an organization scope; Firestore Security Rules are not query filters. See [Firebase's query security guidance](https://firebase.google.com/docs/firestore/security/rules-query).

## Organization bootstrap and membership
1. Bootstrap the first platform administrator out-of-band using a trusted Firebase Admin SDK session. Set the `platformAdmin: true` custom claim; never expose service-account credentials in the client or repository.
2. The platform administrator calls `bootstrapOrganization` to create an organization and its first admin membership.
3. The organization admin or platform administrator calls `setOrganizationMember` to add or suspend organization members.
4. Tenant callables require the active membership and appropriate organization role. Roles include admin, academic_manager, instructor, finance, student, creator and moderator.
5. Users can list only their own organization membership index and switch between organizations they belong to.

Legacy documents without `organizationId` are intentionally denied by the new tenant rules. Before production use, perform a reviewed data migration that assigns the correct organization to every legacy record and tests the migrated data. Do not bulk-assign records to Aptivern without verifying ownership.

## Payment lifecycle
- Paid enrollment starts at `pending_payment`.
- Zero-fee enrollment may start as `active`.
- Payment submission reserves the remaining balance.
- Partial verification reduces the balance but leaves the enrollment pending.
- Full verified payment activates the enrollment in the same Firestore transaction.
- Rejected payments release their reserved amount without increasing paid funds.
- Only authorized organization admins or finance members can verify payments.

Currency amounts are integer MMK. Never store card credentials or secrets.

## Local setup
1. Install Node.js 20+, Flutter stable, Firebase CLI and FlutterFire CLI.
2. Configure a Firebase project; register Web and Android apps.
3. Copy web/.env.example to web/.env.local and add Firebase web config.
4. Run `npm install` in functions and web.
5. Start emulators from this folder: `firebase emulators:start --only auth,firestore,functions`.
6. Run web: `cd web && npm run dev`.
7. Generate the Flutter app in mobile/ and configure it with FlutterFire.

## Release gates
- Bootstrap the first platform admin out-of-band; never trust a role or organization ID sent by a client without checking server-side membership.
- Migrate all existing records to verified organization ownership before deploying the new rules to any existing live database.
- Verify payments against receipts/provider records before marking verified.
- Use synthetic development data; obtain consent before importing student data.
- Run Firestore Rules tests, Functions unit tests, Auth/Firestore/Functions Emulator integration tests, Web build and Mobile build.
- Configure backups, retention, monitoring, App Check, incident contacts and a rollback plan before production.

## Status
Feature branch pilot only. Firebase project credentials, live deployment, real student/payment records and production verification are not configured or claimed.
