#!/usr/bin/env bash
set -euo pipefail

FLUTTER_HOME="${HOME}/.local/share/flutter"
ANDROID_HOME="${HOME}/.android-sdk"
CMDLINE_TOOLS_BUILD="15859902"
CMDLINE_TOOLS_SHA256="4e4c464f145a7512b57d088ac6c278c03c9eea610886b35a5e0804e74eedf583"

sudo apt-get update
sudo apt-get install -y --no-install-recommends curl git unzip zip xz-utils libglu1-mesa

mkdir -p "$(dirname "$FLUTTER_HOME")" "$ANDROID_HOME/cmdline-tools"
if [[ ! -x "$FLUTTER_HOME/bin/flutter" ]]; then
  git clone --depth 1 --branch stable https://github.com/flutter/flutter.git "$FLUTTER_HOME"
fi

TOOLS_ZIP="$(mktemp /tmp/android-cli.XXXXXX.zip)"
TOOLS_TMP="$(mktemp -d /tmp/android-cli.XXXXXX)"
curl -fsSL "https://dl.google.com/android/repository/commandlinetools-linux-${CMDLINE_TOOLS_BUILD}_latest.zip" -o "$TOOLS_ZIP"
echo "${CMDLINE_TOOLS_SHA256}  ${TOOLS_ZIP}" | sha256sum -c -
unzip -q "$TOOLS_ZIP" -d "$TOOLS_TMP"
mkdir -p "$ANDROID_HOME/cmdline-tools/latest"
cp -a "$TOOLS_TMP/cmdline-tools/." "$ANDROID_HOME/cmdline-tools/latest/"
rm -rf "$TOOLS_TMP" "$TOOLS_ZIP"

export FLUTTER_HOME ANDROID_HOME
export PATH="$FLUTTER_HOME/bin:$ANDROID_HOME/cmdline-tools/latest/bin:$ANDROID_HOME/platform-tools:$HOME/.pub-cache/bin:$PATH"
flutter config --android-sdk "$ANDROID_HOME"
yes | sdkmanager --sdk_root="$ANDROID_HOME" --licenses >/dev/null
sdkmanager --sdk_root="$ANDROID_HOME" \
  "platform-tools" \
  "platforms;android-36" \
  "build-tools;36.0.0"
flutter precache --android
flutter doctor --android-licenses

npm install --global firebase-tools
dart pub global activate flutterfire_cli

cat >> "$HOME/.bashrc" <<'EOF'
export FLUTTER_HOME="$HOME/.local/share/flutter"
export ANDROID_HOME="$HOME/.android-sdk"
export ANDROID_SDK_ROOT="$ANDROID_HOME"
export PATH="$FLUTTER_HOME/bin:$ANDROID_HOME/cmdline-tools/latest/bin:$ANDROID_HOME/platform-tools:$HOME/.pub-cache/bin:$PATH"
EOF

echo
echo "Cloud toolchain installed. Open a new terminal, then run:"
echo "  flutter doctor -v"
echo "  firebase --version"
echo "  flutterfire --version"
echo "Then authenticate interactively with: firebase login --no-localhost"
