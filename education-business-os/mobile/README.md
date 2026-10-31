# Flutter mobile client — Aptivern Pilot

The Flutter source lives in this directory. The Android platform folder is generated during CI and must also be generated for a local Android build.

## 1. Generate the Android project

Run from this directory (the trailing dot is important):

```bash
flutter create --platforms=android --project-name aptivern_student_app .
flutter pub get
flutter analyze
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

## 3. Run and verify

```bash
flutter run
flutter test
```

Sign in with a synthetic Firebase Authentication student account. Confirm that only that student's enrollment records appear. Staff mutations must continue to use trusted callable Cloud Functions; do not add direct client writes for payments, attendance, assessments, or outcomes.

## Current scope

The current client is a student sign-in and read-only enrollment starter. Attendance history, payment history, assessments, push notifications, guardian access, and staff workflows still require implementation and acceptance testing. A successful CI APK build proves compilation only; it does not prove Firebase connectivity or a production deployment.
