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
- Mobile: Flutter client scaffold
- Backend: Firebase Auth, Cloud Firestore, Cloud Functions
- Authorization: server-managed custom claims (admin, instructor, student)
- Audit: append-only server-created audit records
- OIA: event integration contract; no live OIA connection is claimed.

## Collections
courses, batches, users, enrollments, payments, attendance, assessments, outcomes, auditLogs.

Currency amounts are integer MMK. Use Firestore timestamps. Never store card credentials or secrets.

## Local setup
1. Install Node.js 20+, Flutter stable, Firebase CLI and FlutterFire CLI.
2. Configure a Firebase project; register Web and Android apps.
3. Copy web/.env.example to web/.env.local and add Firebase web config.
4. Run npm install in functions and web.
5. Start emulators from this folder: firebase emulators:start --only auth,firestore,functions.
6. Run web: cd web && npm run dev.
7. Generate the Flutter app in mobile/ and configure it with FlutterFire.

## Release gates
- Assign custom claims server-side; never trust a role sent by the client.
- Verify payments against receipts/provider records before marking verified.
- Use synthetic development data; obtain consent before importing student data.
- Run emulator rules tests, Functions tests, Web build and Mobile build.
- Configure backups, retention, monitoring and incident contacts before production.

## Status
Scaffold committed to a feature branch. Firebase project credentials, deployment, live data and production verification are not configured or claimed.
