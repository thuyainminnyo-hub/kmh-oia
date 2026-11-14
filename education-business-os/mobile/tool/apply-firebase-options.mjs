#!/usr/bin/env node
/**
 * Wire FlutterFire-generated platform options into the Aptivern Flutter entrypoint.
 * Safe to run repeatedly. Never fabricates Firebase configuration.
 */
import { readFileSync, writeFileSync, existsSync } from "node:fs";
import { resolve } from "node:path";

const optionsPath = resolve("lib/firebase_options.dart");
const mainPath = resolve("lib/main.dart");

if (!existsSync(optionsPath)) {
  console.log("PENDING: lib/firebase_options.dart is missing; main.dart was not modified.");
  process.exit(0);
}
if (!existsSync(mainPath)) {
  console.error("FAIL: lib/main.dart is missing.");
  process.exit(1);
}

let source = readFileSync(mainPath, "utf8");
const optionsImport = "import 'firebase_options.dart';";
const coreImport = "import 'package:firebase_core/firebase_core.dart';";
const initializeCall = "await Firebase.initializeApp();";

if (source.includes("DefaultFirebaseOptions.currentPlatform")) {
  if (!source.includes(optionsImport)) {
    console.error("FAIL: DefaultFirebaseOptions is referenced without the firebase_options.dart import.");
    process.exit(1);
  }
  console.log("PASS: main.dart already uses FlutterFire platform options.");
  process.exit(0);
}

if (!source.includes(coreImport)) {
  console.error("FAIL: firebase_core import was not found in main.dart.");
  process.exit(1);
}
if (!source.includes(initializeCall)) {
  console.error("FAIL: expected Firebase.initializeApp() call was not found; review main.dart manually.");
  process.exit(1);
}

source = source.replace(coreImport, coreImport + "\n" + optionsImport);
source = source.replace(
  initializeCall,
  "await Firebase.initializeApp(\n    options: DefaultFirebaseOptions.currentPlatform,\n  );"
);
writeFileSync(mainPath, source);
console.log("PASS: main.dart now initializes Firebase with DefaultFirebaseOptions.currentPlatform.");
