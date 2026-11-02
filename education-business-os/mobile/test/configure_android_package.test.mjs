import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { mkdtempSync, mkdirSync, writeFileSync, readFileSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import test from "node:test";

const script = resolve(fileURLToPath(new URL("../tool/configure-android-package.mjs", import.meta.url)));

function fixture() {
  const root = mkdtempSync(join(tmpdir(), "aptivern-package-gate-"));
  const app = join(root, "android/app");
  const kotlinDir = join(app, "src/main/kotlin/com/example/aptivern_student_app");
  const activity = join(kotlinDir, "MainActivity.kt");
  mkdirSync(kotlinDir, { recursive: true });
  writeFileSync(join(app, "build.gradle.kts"), [
    "android {",
    '    namespace = "com.example.aptivern_student_app"',
    "    defaultConfig {",
    '        applicationId = "com.example.aptivern_student_app"',
    "    }",
    "}",
    ""
  ].join("\n"));
  writeFileSync(activity, [
    "package com.example.aptivern_student_app",
    "",
    "import io.flutter.embedding.android.FlutterActivity",
    "class MainActivity: FlutterActivity()",
    ""
  ].join("\n"));
  return { root, gradle: join(app, "build.gradle.kts"), activity };
}

test("unset package is reported as PENDING and does not mutate generated identity", () => {
  const f = fixture();
  try {
    const before = readFileSync(f.gradle, "utf8");
    const result = spawnSync(process.execPath, [script], { cwd: f.root, env: { ...process.env, APTIVERN_ANDROID_PACKAGE_NAME: "" }, encoding: "utf8" });
    assert.equal(result.status, 0, result.stderr);
    assert.match(result.stdout, /PENDING/);
    assert.equal(readFileSync(f.gradle, "utf8"), before);
  } finally { rmSync(f.root, { recursive: true, force: true }); }
});

test("exact registered package updates Gradle namespace, applicationId, and MainActivity", () => {
  const f = fixture();
  try {
    const packageName = "org.aptivern.portal";
    const result = spawnSync(process.execPath, [script], { cwd: f.root, env: { ...process.env, APTIVERN_ANDROID_PACKAGE_NAME: packageName }, encoding: "utf8" });
    assert.equal(result.status, 0, result.stderr);
    assert.match(readFileSync(f.gradle, "utf8"), new RegExp(`namespace = "${packageName}"`));
    assert.match(readFileSync(f.gradle, "utf8"), new RegExp(`applicationId = "${packageName}"`));
    assert.match(readFileSync(f.activity, "utf8"), new RegExp(`^package ${packageName}$`, "m"));
  } finally { rmSync(f.root, { recursive: true, force: true }); }
});

test("placeholder package IDs are rejected", () => {
  const f = fixture();
  try {
    const result = spawnSync(process.execPath, [script], { cwd: f.root, env: { ...process.env, APTIVERN_ANDROID_PACKAGE_NAME: "com.example.aptivern_student_app" }, encoding: "utf8" });
    assert.equal(result.status, 1);
    assert.match(result.stderr, /placeholder/);
  } finally { rmSync(f.root, { recursive: true, force: true }); }
});
