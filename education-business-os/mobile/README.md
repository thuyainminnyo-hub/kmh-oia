# Flutter mobile client — Aptivern Pilot

The Flutter source lives in this directory. The Android platform folder is generated during CI and must also be generated for a local Android build.

## 1. Generate the Android project

Run from this directory (the trailing dot is important):

```bash
flutter create --platforms=android --project-name aptivern_student_app .
flutter pub get
flutter analyze
flutter test
flutter build apk --debug
```

This preserves `lib/main.dart` and creates the native Android Gradle project.

## 2. Connect Firebase

Use the same Firebase project as the Web client:

```bash
dart pub global activate flutterfire_cli
flutterfire configure
```

Register the Android application in Firebase and complete the generated native configuration. The current app calls `Firebase.initializeApp()`, so the Android Firebase configuration must be present before running on a device. Never commit service-account JSON or private credentials.

## 3. Student organization workspace

After sign-in, the app reads only the signed-in user's private membership index:

`userOrganizationMemberships/{uid}/organizations/{organizationId}`

It displays active memberships whose organization role is `student`. A student with more than one school can switch workspaces. Enrollment queries are scoped by both `organizationId` and the authenticated user's `studentId`; do not replace them with an unscoped collection query.

The student client is read-only. Enrollment, payment, attendance, assessment and outcome mutations must continue to use trusted callable Cloud Functions with server-side organization membership checks. Never accept an organization role or membership status supplied only by the client.

## 4. Run and verify

```bash
flutter run
flutter test
```

Use synthetic Firebase Authentication accounts with an active student membership in the demo organization. Verify:
- A student sees only their own enrollments in the selected organization.
- Switching to another active organization changes the query scope.
- A student with no active student membership sees an onboarding/help message rather than cross-organization records.
- Suspended memberships are not shown as active workspaces.
- A direct, unscoped read is denied by Firestore Rules.

## Current scope

This client provides sign-in, organization selection and read-only enrollment display. Attendance history, payment history, assessments, assignments, Creative Writing, push notifications, guardian access, offline work recovery and creator tools still require implementation and acceptance testing. A successful CI APK build proves compilation only; it does not prove device Firebase connectivity or production deployment.


## Phase 13.6 cloud Firebase configuration

See [PHASE-13.6-CLOUD-SETUP.md](PHASE-13.6-CLOUD-SETUP.md) for the Codespaces toolchain, existing Firebase Android app inspection, package ID matching, FlutterFire configuration, and acceptance evidence. The CI package gate uses the repository Actions variable `APTIVERN_ANDROID_PACKAGE_NAME`; leave it unset until the existing Firebase Android package has been confirmed. An unset variable is reported as PENDING, not as a verified Firebase registration.
