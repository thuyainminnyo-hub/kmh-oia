#!/usr/bin/env node
/** Phase 13.6 cloud Android package identity gate. */
import { readFileSync, existsSync } from "node:fs";
import { resolve } from "node:path";

const org = (process.env.APTIVERN_ANDROID_ORG ?? "").trim();
const paths = [resolve("android/app/build.gradle.kts"), resolve("android/app/build.gradle")];
const gradlePath = paths.find(existsSync);
if (!gradlePath) { console.error("FAIL: Android Gradle app module is missing."); process.exit(1); }
const gradle = readFileSync(gradlePath, "utf8");
const match = gradle.match(/applicationId\s*(?:=\s*)?["\']([^"\']+)["\']/);
if (!match) { console.error("FAIL: applicationId could not be read."); process.exit(1); }
const actual = match[1];
if (!org) {
  console.log("PENDING: APTIVERN_ANDROID_ORG is not configured.");
  console.log(`Detected generated Android applicationId: ${actual}`);
  console.log("Compare with firebase apps:list before registering or configuring an app.");
  process.exit(0);
}
if (!/^[a-zA-Z][a-zA-Z0-9]*(\.[a-zA-Z][a-zA-Z0-9_]*)+$/.test(org) || org === "com.example" || org.endsWith(".example")) {
  console.error("FAIL: APTIVERN_ANDROID_ORG must be a real reverse-DNS organization, not a placeholder.");
  process.exit(1);
}
const expected = `${org}.aptivern_student_app`;
if (actual !== expected) {
  console.error("FAIL: Android applicationId does not match the configured Firebase package.");
  console.error(`Expected: ${expected}`);
  console.error(`Actual:   ${actual}`);
  process.exit(1);
}
console.log("PASS: Android applicationId matches APTIVERN_ANDROID_ORG.");
console.log(`Android applicationId: ${actual}`);
