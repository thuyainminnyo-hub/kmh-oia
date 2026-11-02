#!/usr/bin/env node
/**
 * Phase 13.6 Android Firebase configuration preflight.
 * Run from education-business-os/mobile after FlutterFire configuration.
 * This validates public Firebase client configuration; it never prints API keys.
 */
import { readFileSync, existsSync } from "node:fs";
import { resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const mobileDir = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const expectedProjectId = "aptivern-education-os";
const expectedProjectNumber = "1068042057781";
const configPath = resolve(mobileDir, "android/app/google-services.json");
const gradleKtsPath = resolve(mobileDir, "android/app/build.gradle.kts");
const gradleGroovyPath = resolve(mobileDir, "android/app/build.gradle");

function fail(message) {
  console.error(`FAIL: ${message}`);
  process.exit(1);
}

if (!existsSync(configPath)) {
  fail("android/app/google-services.json is missing. Run flutterfire configure for the registered Android app.");
}

const gradlePath = existsSync(gradleKtsPath)
  ? gradleKtsPath
  : existsSync(gradleGroovyPath)
    ? gradleGroovyPath
    : null;

if (!gradlePath) {
  fail("Android app Gradle file is missing. Generate the Android project before running this check.");
}

let config;
try {
  config = JSON.parse(readFileSync(configPath, "utf8"));
} catch {
  fail("google-services.json is not valid JSON.");
}

if (config.project_info?.project_id !== expectedProjectId) {
  fail(`Firebase project_id must be ${expectedProjectId}.`);
}
if (String(config.project_info?.project_number) !== expectedProjectNumber) {
  fail(`Firebase project_number must be ${expectedProjectNumber}.`);
}

const gradle = readFileSync(gradlePath, "utf8");
if (!gradle.includes("com.google.gms.google-services")) {
  fail("Google Services Gradle plugin is not applied in the Android app module.");
}

const appIdMatch = gradle.match(/applicationId\\s*(?:=\\s*)?["']([^"']+)["']/);
if (!appIdMatch) {
  fail("Could not read applicationId from the Android app Gradle file.");
}
const packageName = appIdMatch[1];

const client = (config.client ?? []).find(
  (entry) => entry.client_info?.android_client_info?.package_name === packageName
);
if (!client) {
  fail(`google-services.json has no Android client matching applicationId ${packageName}.`);
}
if (!client.client_info?.mobilesdk_app_id) {
  fail("Matching Android client is missing mobilesdk_app_id.");
}
if (!Array.isArray(client.api_key) || !client.api_key.some((key) => key.current_key)) {
  fail("Matching Android client is missing an API key entry.");
}

console.log("PASS: Android Firebase configuration matches the expected project.");
console.log(`Project: ${expectedProjectId} (${expectedProjectNumber})`);
console.log(`Android package: ${packageName}`);
console.log(`Firebase Android App ID: ${client.client_info.mobilesdk_app_id}`);
console.log("API key: present (value intentionally not displayed)");
console.log("Google Services Gradle plugin: applied");
