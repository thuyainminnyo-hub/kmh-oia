import { readFile } from "node:fs/promises";
import { after, before, test } from "node:test";
import assert from "node:assert/strict";
import {
  assertFails, assertSucceeds, initializeTestEnvironment
} from "@firebase/rules-unit-testing";
import { doc, getDoc, setDoc } from "firebase/firestore";

const projectId = "demo-education-business-os";
let env;

before(async () => {
  const rules = await readFile(new URL("../firestore.rules", import.meta.url), "utf8");
  env = await initializeTestEnvironment({ projectId, firestore: { rules } });
  await env.withSecurityRulesDisabled(async (context) => {
    const db = context.firestore();
    await setDoc(doc(db, "enrollments/enr-a"), {
      studentId: "student-a", instructorId: "teacher-a", batchId: "APT-FLUTTER-B5", status: "active"
    });
    await setDoc(doc(db, "enrollments/enr-b"), {
      studentId: "student-b", instructorId: "teacher-a", batchId: "APT-FLUTTER-B5", status: "active"
    });
    await setDoc(doc(db, "payments/pay-a"), { studentId: "student-a", instructorId: "teacher-a", status: "pending" });
  });
});

after(async () => { await env.cleanup(); });

test("student can read own enrollment", async () => {
  const db = env.authenticatedContext("student-a", { role: "student" }).firestore();
  await assertSucceeds(getDoc(doc(db, "enrollments/enr-a")));
});

test("student cannot read another student's enrollment", async () => {
  const db = env.authenticatedContext("student-a", { role: "student" }).firestore();
  await assertFails(getDoc(doc(db, "enrollments/enr-b")));
});

test("student cannot write payment records directly", async () => {
  const db = env.authenticatedContext("student-a", { role: "student" }).firestore();
  await assertFails(setDoc(doc(db, "payments/forged"), { studentId: "student-a", amount: 300000 }));
});

test("unauthenticated users cannot read course data", async () => {
  const db = env.unauthenticatedContext().firestore();
  await assertFails(getDoc(doc(db, "courses/flutter-foundation")));
});

test("student cannot promote own role", async () => {
  const db = env.authenticatedContext("student-a", { role: "student" }).firestore();
  await assertFails(setDoc(doc(db, "users/student-a"), {
    displayName: "Student", email: "student@example.com", role: "admin"
  }));
});
