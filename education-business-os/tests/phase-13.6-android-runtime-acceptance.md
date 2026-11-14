# Phase 13.6 — Android Real-Device Runtime Acceptance

## Scope

Verify the Aptivern Student Android client against the configured Firebase project before enabling App Check enforcement.

## Known project identity

- Firebase project ID: `aptivern-education-os`
- Firebase project number: `1068042057781`
- Firebase Hosting origin: `https://aptivern-education-os.web.app`
- Android package name: pending confirmation from the registered Android app
- Firebase Android App ID: pending local configuration inspection
- SHA-256 signing fingerprints: pending debug/release signing report
- Play Integrity Cloud project linkage: pending Firebase/Google Play Console confirmation

Firebase client configuration files contain project/app identifiers, not service-account credentials. Never add service-account private keys, debug App Check tokens, or other private credentials to this repository.

## Gate 13.6.1 — Local Android Firebase configuration

From `education-business-os/mobile`:

```bash
flutter create --platforms=android --project-name aptivern_student_app .
dart pub global activate flutterfire_cli
flutterfire configure --project=aptivern-education-os --platforms=android
node tool/verify-firebase-config.mjs
```

The preflight verifies:

- `android/app/google-services.json` exists and is valid JSON.
- Project ID and project number match the known Aptivern Firebase project.
- The Google Services Gradle plugin is applied.
- The Gradle `applicationId` matches an Android client in `google-services.json`.
- The matching Android client has an App ID and API key entry (the key value is never printed).

## Gate 13.6.2 — Signing and Play Integrity

From `education-business-os/mobile/android`:

```bash
./gradlew signingReport
```

Record SHA-256 fingerprints for the debug certificate and the release certificate used for distribution. If distributed through Google Play, also verify the Play App Signing certificate fingerprint in Play Console.

In Google Play Console, verify that the Play Integrity API is linked to the same Google Cloud project as Firebase project `aptivern-education-os`. Register the Android app in Firebase App Check with Play Integrity using the correct signing fingerprint.

## Gate 13.6.3 — Device smoke test

Use a synthetic Firebase Auth account and a physical Android device:

- [ ] Install the debug APK.
- [ ] App starts without Firebase initialization errors.
- [ ] Sign-in succeeds.
- [ ] App Check debug token is generated and registered privately in Firebase Console.
- [ ] App Check token retrieval succeeds.
- [ ] Active student membership is loaded.
- [ ] Organization switching only shows active student memberships.
- [ ] Enrollment query is scoped by both organization ID and student UID.
- [ ] Sign-out succeeds.

## Gate 13.6.4 — Negative security tests

- [ ] Unauthenticated access is denied.
- [ ] Suspended membership cannot access the organization.
- [ ] A user cannot read another student's enrollment.
- [ ] Organization A cannot read Organization B data.
- [ ] Invalid/missing App Check tokens are rejected after enforcement is enabled in a controlled test environment.

## Evidence record

| Evidence | Status |
|---|---|
| Existing CI debug APK build | PASS — run 41389738535 |
| Local Firebase config preflight | NOT RUN — requires configured local Android project |
| Package ID / Android App ID | NOT RECORDED |
| Debug/release SHA-256 | NOT RECORDED |
| Play Integrity linkage | NOT VERIFIED |
| Physical-device smoke test | NOT RUN |
| App Check token runtime test | NOT RUN |
| Production enforcement | NOT ENABLED |

## Acceptance decision

Phase 13.6 remains **IN PROGRESS** until the local preflight, signing verification, Play Integrity registration, and physical-device smoke test have attached evidence. CI APK compilation alone is not runtime or production evidence.
