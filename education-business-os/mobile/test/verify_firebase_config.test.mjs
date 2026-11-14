import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { mkdtempSync, mkdirSync, writeFileSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import test from "node:test";

const verifier = resolve(fileURLToPath(new URL("../tool/verify-firebase-config.mjs", import.meta.url)));
const expectedProject = "aptivern-education-os";
const expectedNumber = "1068042057781";
const expectedPackage = "org.aptivern.portal";
const expectedAppId = "1:1068042057781:android:abc123def456";

function fixture({ options = true, projectId = expectedProject, senderId = expectedNumber, appId = expectedAppId } = {}) {
  const root = mkdtempSync(join(tmpdir(), "aptivern-firebase-config-"));
  const lib = join(root, "lib");
  const androidApp = join(root, "android/app");
  mkdirSync(lib, { recursive: true });
  mkdirSync(androidApp, { recursive: true });

  if (options) {
    const dart = [
      "class DefaultFirebaseOptions {",
      "  static const FirebaseOptions android = FirebaseOptions(",
      "    apiKey: 'test-api-key-not-real',",
      "    appId: '" + appId + "',",
      "    messagingSenderId: '" + senderId + "',",
      "    projectId: '" + projectId + "',",
      "  );",
      "}"
    ].join("\n");
    writeFileSync(join(lib, "firebase_options.dart"), dart);
  }

  writeFileSync(
    join(androidApp, "build.gradle.kts"),
    [
      "android {",
      '  namespace = "' + expectedPackage + '"',
      "  defaultConfig {",
      '    applicationId = "' + expectedPackage + '"',
      "  }",
      "}"
    ].join("\n")
  );

  return root;
}

function runVerifier(cwd, packageName = expectedPackage) {
  return spawnSync(process.execPath, [verifier], {
    cwd,
    encoding: "utf8",
    env: {
      ...process.env,
      APTIVERN_ANDROID_PACKAGE_NAME: packageName
    }
  });
}

test("missing generated options reports PENDING without exposing credentials", () => {
  const root = fixture({ options: false });
  try {
    const result = runVerifier(root);
    assert.equal(result.status, 2);
    assert.match(result.stderr, /PENDING/);
    assert.doesNotMatch(result.stdout + result.stderr, /test-api-key-not-real/);
  } finally {
    rmSync(root, { recursive: true, force: true });
  }
});

test("valid FlutterFire Android options pass for the expected Firebase project", () => {
  const root = fixture();
  try {
    const result = runVerifier(root);
    assert.equal(result.status, 0, result.stderr);
    assert.match(result.stdout, /PASS: FlutterFire Android options belong to the expected Firebase project/);
    assert.match(result.stdout, new RegExp(expectedAppId));
    assert.doesNotMatch(result.stdout, /test-api-key-not-real/);
  } finally {
    rmSync(root, { recursive: true, force: true });
  }
});

test("wrong Firebase project ID is rejected", () => {
  const root = fixture({ projectId: "wrong-firebase-project" });
  try {
    const result = runVerifier(root);
    assert.equal(result.status, 1);
    assert.match(result.stderr, /projectId must be aptivern-education-os/);
  } finally {
    rmSync(root, { recursive: true, force: true });
  }
});

test("wrong Firebase project number is rejected", () => {
  const root = fixture({ senderId: "999999999999" });
  try {
    const result = runVerifier(root);
    assert.equal(result.status, 1);
    assert.match(result.stderr, /messagingSenderId must be 1068042057781/);
  } finally {
    rmSync(root, { recursive: true, force: true });
  }
});

test("package mismatch is rejected", () => {
  const root = fixture();
  try {
    const result = runVerifier(root, "org.other.portal");
    assert.equal(result.status, 1);
    assert.match(result.stderr, /does not match APTIVERN_ANDROID_PACKAGE_NAME/);
  } finally {
    rmSync(root, { recursive: true, force: true });
  }
});
