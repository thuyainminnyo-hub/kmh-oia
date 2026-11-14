import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { mkdtempSync, mkdirSync, writeFileSync, readFileSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import test from "node:test";

const script = resolve(fileURLToPath(new URL("../tool/apply-firebase-options.mjs", import.meta.url)));
const baseMain = [
  "import 'package:firebase_core/firebase_core.dart';",
  "import 'package:flutter/material.dart';",
  "",
  "Future<void> main() async {",
  "  WidgetsFlutterBinding.ensureInitialized();",
  "  await Firebase.initializeApp();",
  "  await activateAptivernAppCheck();",
  "}",
  ""
].join("\n");

function fixture(withOptions = true) {
  const root = mkdtempSync(join(tmpdir(), "aptivern-firebase-options-"));
  const lib = join(root, "lib");
  mkdirSync(lib, { recursive: true });
  writeFileSync(join(lib, "main.dart"), baseMain);
  if (withOptions) {
    writeFileSync(join(lib, "firebase_options.dart"), "// generated fixture; no real credentials\n");
  }
  return { root, main: join(lib, "main.dart") };
}

test("missing generated options reports PENDING without mutating main.dart", () => {
  const f = fixture(false);
  try {
    const before = readFileSync(f.main, "utf8");
    const result = spawnSync(process.execPath, [script], { cwd: f.root, encoding: "utf8" });
    assert.equal(result.status, 0, result.stderr);
    assert.match(result.stdout, /PENDING/);
    assert.equal(readFileSync(f.main, "utf8"), before);
  } finally {
    rmSync(f.root, { recursive: true, force: true });
  }
});

test("generated options wire initializeApp to currentPlatform", () => {
  const f = fixture(true);
  try {
    const result = spawnSync(process.execPath, [script], { cwd: f.root, encoding: "utf8" });
    assert.equal(result.status, 0, result.stderr);
    const updated = readFileSync(f.main, "utf8");
    assert.match(updated, /import 'firebase_options\.dart';/);
    assert.match(updated, /options: DefaultFirebaseOptions\.currentPlatform/);
    assert.ok(updated.indexOf("Firebase.initializeApp") < updated.indexOf("activateAptivernAppCheck"));
  } finally {
    rmSync(f.root, { recursive: true, force: true });
  }
});

test("running the wiring script twice is idempotent", () => {
  const f = fixture(true);
  try {
    const first = spawnSync(process.execPath, [script], { cwd: f.root, encoding: "utf8" });
    assert.equal(first.status, 0, first.stderr);
    const firstContent = readFileSync(f.main, "utf8");
    const second = spawnSync(process.execPath, [script], { cwd: f.root, encoding: "utf8" });
    assert.equal(second.status, 0, second.stderr);
    assert.match(second.stdout, /already uses FlutterFire/);
    assert.equal(readFileSync(f.main, "utf8"), firstContent);
  } finally {
    rmSync(f.root, { recursive: true, force: true });
  }
});
