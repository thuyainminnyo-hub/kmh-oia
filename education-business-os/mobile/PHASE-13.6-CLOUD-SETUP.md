# Phase 13.6 — Cloud Firebase Android registration

This workflow deliberately does not guess an Android package ID or create a second Firebase Android app. Inspect the existing Firebase registration first.

## 1. Open the feature branch in GitHub Codespaces

Create a Codespace on `feat/education-business-os-aptivern-pilot` from the repository's Code → Codespaces menu. Wait for the post-create setup to finish, then open a **new terminal**.

## 2. Verify the cloud toolchain and authenticate interactively

The repository-root `.devcontainer` setup provisions Flutter stable, Android command-line tools, Java 21, Firebase CLI, and FlutterFire CLI. Do not repeat the manual apt/clone installation unless the automated setup failed.

From the repository root:

```bash
.devcontainer/check-toolchain.sh
firebase login --no-localhost
firebase projects:list
```

Confirm that `aptivern-education-os` is visible in the project list. If it is absent, stop and resolve Google account/project access before proceeding. Do not paste access tokens or credentials into chat.

## 3. Inspect Firebase registrations before generating Android

From the mobile directory:

```bash
cd education-business-os/mobile
firebase apps:list --project aptivern-education-os
```

Record the existing Android app's package name and Firebase App ID. Do not paste API keys, access tokens, or service-account credentials into chat.

Then inspect the generated Android package:

```bash
flutter create --platforms=android --project-name aptivern_student_app .
grep -nE 'namespace|applicationId' android/app/build.gradle.kts android/app/build.gradle 2>/dev/null
```

Compare Firebase package name with Gradle `applicationId`. Do not create another Firebase app if an existing registration is the intended app.

## 4. Set the Cloud CI variable only after comparison

The workflow expects the full, exact registered Android package name in GitHub repository variable `APTIVERN_ANDROID_PACKAGE_NAME`.

For example, if (and only if) Firebase shows `org.example.aptivern_student_app`, the variable would be `org.example.aptivern_student_app`. This is an illustration, not the real value.

Set it at GitHub repository Settings → Secrets and variables → Actions → Variables → New repository variable. It is a package identifier, not a secret.

CI derives `APTIVERN_ANDROID_PACKAGE_NAME` exactly as supplied and fails on a mismatch or placeholder `com.example`. Until the variable is set, CI reports the package gate as PENDING and does not claim Firebase package verification.

## 5. Run FlutterFire against the existing registration

Only after confirming the package name:

```bash
flutter pub get
flutterfire configure \
  --project=aptivern-education-os \
  --platforms=android \
  --android-package-name '<EXACT_EXISTING_FIREBASE_PACKAGE_NAME>'
```

Copy the exact package argument from `firebase apps:list --project aptivern-education-os` or Firebase Project Settings → Your apps. Stop if the CLI proposes creating an unintended duplicate.

Expected output includes `lib/firebase_options.dart` and, when native Gradle configuration is applied, `android/app/google-services.json`.

## 6. Initialize Firebase explicitly

In `lib/main.dart`, import `firebase_options.dart` and initialize with `DefaultFirebaseOptions.currentPlatform` before activating App Check and before any Auth/Firestore access:

```dart
await Firebase.initializeApp(
  options: DefaultFirebaseOptions.currentPlatform,
);
await activateAptivernAppCheck();
```

## 7. Verify locally in Codespaces

```bash
node tool/verify-android-package.mjs
node tool/verify-firebase-config.mjs
flutter pub get
flutter analyze
flutter test
flutter build apk --debug
cd android && ./gradlew signingReport
```

The Firebase preflight requires a real `google-services.json`; do not fabricate one. Keep service-account keys, release keystores, passwords, and App Check debug tokens out of Git.

## 8. Evidence boundary

A successful cloud APK build proves compilation only. It does not prove Firebase runtime connectivity, App Check token acceptance, Play Integrity, or physical-device behavior.

## GitHub Codespaces — one-click cloud toolchain

This branch includes `.devcontainer/devcontainer.json`. Create a Codespace on this feature branch and let its post-create setup finish. It installs Flutter stable, Android command-line tools (with a checksum check), Java 21, Firebase CLI, and FlutterFire CLI. GitHub documents this devcontainer configuration pattern and its post-create hook.

After the Codespace opens, start a fresh terminal and run:

```bash
.devcontainer/check-toolchain.sh
firebase login --no-localhost
cd education-business-os/mobile
firebase apps:list --project aptivern-education-os
```

Inspect the existing Android package name and Firebase App ID before generating or configuring a native Android app. FlutterFire's setup guide says it attempts to match apps already registered in the selected Firebase project using the current Flutter project configuration, but its workflow can create a Firebase app for a selected platform if no match is found. Do not accept a create-new-app prompt until the existing registrations have been checked.

Once the existing package is confirmed, generate the Android scaffold with the correct `applicationId`/`namespace`, set repository variable `APTIVERN_ANDROID_PACKAGE_NAME` to that exact full package ID, and then run the FlutterFire configure command in section 5.

Firebase sign-in is intentionally interactive and is not performed by the Codespaces bootstrap script. Do not put Firebase access tokens, App Check debug tokens, service-account keys, or signing keystores in the repository.
