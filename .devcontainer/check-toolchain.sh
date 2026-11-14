#!/usr/bin/env bash
set -euo pipefail

for tool in flutter dart firebase flutterfire java adb sdkmanager; do
  if ! command -v "$tool" >/dev/null 2>&1; then
    echo "FAIL: required tool not found: $tool" >&2
    exit 1
  fi
done

echo "Flutter: $(flutter --version | head -n 1)"
echo "Dart: $(dart --version 2>&1)"
echo "Firebase CLI: $(firebase --version)"
echo "FlutterFire CLI: $(flutterfire --version)"
echo "Java: $(java -version 2>&1 | head -n 1)"
echo "ADB: $(adb version | head -n 1)"
echo "Android SDK: ${ANDROID_HOME:-not-set}"
flutter doctor -v
