# Flutter mobile client — Aptivern Pilot

Create the Flutter client in this folder with Flutter stable:

    flutter create aptivern_student_app

Configure Firebase using FlutterFire CLI and add firebase_core, firebase_auth, cloud_firestore and cloud_functions. Use the same Firebase project as the Web client.

Implement sign-in and read-only student enrollment first. Staff write actions must follow role rules and trusted server functions. Never commit google-services.json, GoogleService-Info.plist, service-account JSON or local secrets.
