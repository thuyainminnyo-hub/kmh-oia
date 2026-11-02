# Phase 13.6 — Cloud Firebase Android registration

This workflow deliberately does not guess an Android package ID or create a second Firebase Android app. Inspect the existing Firebase registration first.

## 1. Open the feature branch in GitHub Codespaces

Create a Codespace on `feat/education-business-os-aptivern-pilot`, then open a terminal.

## 2. Install and authenticate the toolchain

```bash
sudo apt-get update
sudo apt-get install -y curl git unzip zip xz-utils libglu1-mesa openjdk-21-jdk

git clone https://github.com/flutter/flutter.git -b stable "$HOME/development/flutter"
export PATH="$HOME/development/flutter/bin:$PATH"
echo 'export PATH="$HOME/development/flutter/bin:$PATH"' >> ~/.bashrc
flutter doctor -v

npm install -g firebase-tools
firebase login --no-localhost

dart pub global activate flutterfire_cli
export PATH="$PATH:$HOME/.pub-cache/bin"
echo 'export PATH="$PATH:$HOME/.pub-cache/bin"' >> ~/.bashrc

firebase --version
flutter --version
flutterfire --version
```

## 3. Inspect Firebase registrations before generating Android

From the mobile directory:

```bash
cd education-business-os/mobile
firebase apps:list ANDROID --project aptivern-education-os
```

Record the existing Android app's package name and Firebase App ID. Do not paste API keys, access tokens, or service-account credentials into chat.

Then inspect the generated Android package:

```bash
flutter create --platforms=android --project-name aptivern_student_app .
grep -nE 'namespace|applicationId' android/app/build.gradle.kts android/app/build.gradle 2>/dev/null
```

Compare Firebase package name with Gradle `applicationId`. Do not create another Firebase app if an existing registration is the intended app.

## 4. Set the Cloud CI variable only after comparison

The workflow expects the reverse-DNS organization part of the confirmed package name in GitHub repository variable `APTIVERN_ANDROID_ORG`.

For example, if (and only if) Firebase shows `org.example.aptivern_student_app`, the variable would be `org.example`. This is an illustration, not the real value.

Set it at GitHub repository Settings → Secrets and variables → Actions → Variables → New repository variable. It is a package identifier, not a secret.

CI derives `<APTIVERN_ANDROID_ORG>.aptivern_student_app` and fails on a mismatch or placeholder `com.example`. Until the variable is set, CI reports the package gate as PENDING and does not claim Firebase package verification.

## 5. Run FlutterFire against the existing registration

Only after confirming the package name:

```bash
flutter pub get
flutterfire configure \
  --project=aptivern-education-os \
  --platforms=android \
  --android-package-name '<EXACT_EXISTING_FIREBASE_PACKAGE_NAME>'
```

Copy the exact package argument from `firebase apps:list ANDROID` or Firebase Project Settings → Your apps. Stop if the CLI proposes creating an unintended duplicate.

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
