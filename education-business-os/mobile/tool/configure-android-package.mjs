#!/usr/bin/env node
/**
 * Apply the exact Firebase-registered Android package ID to generated Flutter scaffolding.
 * No package is guessed: when the environment variable is absent, this is a no-op.
 */
import { readFileSync, writeFileSync, existsSync, readdirSync } from "node:fs";
import { resolve, join } from "node:path";

const target = (process.env.APTIVERN_ANDROID_PACKAGE_NAME ?? "").trim();
const gradleCandidates = [resolve("android/app/build.gradle.kts"), resolve("android/app/build.gradle")];
const gradlePath = gradleCandidates.find(existsSync);
if (!gradlePath) { console.error("FAIL: Android Gradle app module is missing."); process.exit(1); }

if (!target) {
  console.log("PENDING: APTIVERN_ANDROID_PACKAGE_NAME is unset; generated Android identity was not modified.");
  process.exit(0);
}

const packagePattern = /^[a-z][a-z0-9_]*(?:\.[a-z][a-z0-9_]*)+$/;
if (!packagePattern.test(target) || target === "com.example" || target.startsWith("com.example.")) {
  console.error("FAIL: APTIVERN_ANDROID_PACKAGE_NAME must be the exact registered Android package ID, not a placeholder.");
  process.exit(1);
}

let gradle = readFileSync(gradlePath, "utf8");
const valuePattern = /^(\s*(?:namespace|applicationId)\s*(?:=\s*)?)(["'])([^"']+)\2\s*$/;
function setGradleValue(source, key) {
  const lines = source.split(/\r?\n/);
  const index = lines.findIndex((line) => {
    const trimmed = line.trimStart();
    return trimmed.startsWith(`${key} `) || trimmed.startsWith(`${key}=`);
  });
  if (index < 0 || !valuePattern.test(lines[index])) {
    console.error(`FAIL: ${key} was not found as a string property in ${gradlePath}.`);
    process.exit(1);
  }
  lines[index] = lines[index].replace(valuePattern, (_match, prefix, quote) => `${prefix}${quote}${target}${quote}`);
  return lines.join("\n");
}
gradle = setGradleValue(gradle, "namespace");
gradle = setGradleValue(gradle, "applicationId");
writeFileSync(gradlePath, gradle);

function findMainActivities(directory) {
  if (!existsSync(directory)) return [];
  const found = [];
  for (const entry of readdirSync(directory, { withFileTypes: true })) {
    const path = join(directory, entry.name);
    if (entry.isDirectory()) found.push(...findMainActivities(path));
    else if (entry.isFile() && /^MainActivity\.(kt|java)$/.test(entry.name)) found.push(path);
  }
  return found;
}
const activityFiles = [
  ...findMainActivities(resolve("android/app/src/main/kotlin")),
  ...findMainActivities(resolve("android/app/src/main/java")),
];
if (activityFiles.length === 0) {
  console.error("FAIL: Generated Android MainActivity source was not found.");
  process.exit(1);
}
for (const file of activityFiles) {
  let source = readFileSync(file, "utf8");
  const packagePattern = /^package\s+[A-Za-z0-9_.]+\s*;?\s*$/m;
  if (!packagePattern.test(source)) {
    console.error(`FAIL: MainActivity package declaration missing in ${file}.`);
    process.exit(1);
  }
  source = source.replace(packagePattern, `package ${target}`);
  writeFileSync(file, source);
}

console.log("PASS: Android namespace, applicationId, and MainActivity package updated.");
console.log(`Android package: ${target}`);
