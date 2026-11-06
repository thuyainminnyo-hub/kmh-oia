#!/usr/bin/env node
/**
 * Validate the FlutterFire-generated Dart configuration for the Aptivern Android app.
 * FlutterFire uses DefaultFirebaseOptions; google-services.json is not required by this gate.
 * Never print Firebase API key values.
 */
import { readFileSync, existsSync } from "node:fs";
import { resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const mobileDir = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const expectedProjectId = "aptivern-education-os";
const expectedProjectNumber = "1068042057781";
const optionsPath = resolve(mobileDir, "lib/firebase_options.dart");
const gradlePaths = [
  resolve(mobileDir, "android/app/build.gradle.kts"),
  resolve(mobileDir, "android/app/build.gradle"),
];

function fail(message) {
  console.error(`FAIL: ${message}`);
  process.exit(1);
}

if (!existsSync(optionsPath)) {
  console.error("PENDING: lib/firebase_options.dart is missing. Run FlutterFire configure against the existing Firebase Android app.");
  process.exit(2);
}

const gradlePath = gradlePaths.find(existsSync);
if (!gradlePath) fail("Android app Gradle file is missing. Generate Android scaffolding first.");

const source = readFileSync(optionsPath, "utf8");
const androidBlock = source.match(/(?:static\s+)?const\s+FirebaseOptions\s+android\s*=\s*FirebaseOptions\(([\s\S]*?)\);/);
if (!androidBlock) fail("firebase_options.dart has no generated Android FirebaseOptions block.");

function readDartString(block, key) {
  const match = block.match(new RegExp(`\\b${key}\\s*:\\s*[\\\']([^\\\']+)[\\\']`));
  return match?.[1] ?? null;
}

const androidOptions = androidBlock[1];
const projectId = readDartString(androidOptions, "projectId");
const senderId = readDartString(androidOptions, "messagingSenderId");
const appId = readDartString(androidOptions, "appId");
if (projectId !== expectedProjectId) fail(`Android Firebase projectId must be ${expectedProjectId}.`);
if (senderId !== expectedProjectNumber) fail(`Android Firebase messagingSenderId must be ${expectedProjectNumber}.`);
if (!appId || !new RegExp(`^1:${expectedProjectNumber}:android:[A-Za-z0-9_-]+$`).test(appId)) {
  fail("Android Firebase appId is missing or does not belong to the expected Firebase project.");
}

const gradle = readFileSync(gradlePath, "utf8");
const packageMatch = gradle.match(/applicationId\s*(?:=\s*)?["\']([^"\']+)["\']/);
if (!packageMatch) fail("Could not read applicationId from the Android app Gradle file.");
const actualPackage = packageMatch[1];
const expectedPackage = (process.env.APTIVERN_ANDROID_PACKAGE_NAME ?? "").trim();
if (expectedPackage && actualPackage !== expectedPackage) {
  fail(`Android applicationId ${actualPackage} does not match APTIVERN_ANDROID_PACKAGE_NAME.`);
}
if (!expectedPackage) console.log("PENDING: repository package variable is unset; Android package registration identity has not been independently asserted.");

console.log("PASS: FlutterFire Android options belong to the expected Firebase project.");
console.log(`Project: ${projectId} (${senderId})`);
console.log(`Firebase Android App ID: ${appId}`);
console.log(`Android applicationId: ${actualPackage}`);
console.log("API key: present only if generated options contain it; value intentionally not displayed.");
