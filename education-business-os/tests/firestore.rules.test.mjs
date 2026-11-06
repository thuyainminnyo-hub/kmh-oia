import { readFile } from "node:fs/promises";
import { after, before, test } from "node:test";
import assert from "node:assert/strict";
import {
  assertFails, assertSucceeds, initializeTestEnvironment
} from "@firebase/rules-unit-testing";
import { collection, doc, getDoc, getDocs, query, setDoc, where } from "firebase/firestore";

const projectId = "demo-education-business-os";
let env;

before(async () => {
  const rules = await readFile(new URL("../firestore.rules", import.meta.url), "utf8");
  env = await initializeTestEnvironment({ projectId, firestore: { rules } });
  await env.withSecurityRulesDisabled(async (context) => {
    const db = context.firestore();
    const memberships = [
      ["org-a", "admin-a", "admin"],
      ["org-a", "student-a", "student"],
      ["org-a", "student-c", "student"],
      ["org-a", "teacher-a", "instructor"],
      ["org-a", "teacher-c", "instructor"],
      ["org-a", "finance-a", "finance"],
      ["org-b", "admin-b", "admin"],
      ["org-b", "student-b", "student"],
      ["org-b", "teacher-b", "instructor"]
    ];
    await setDoc(doc(db, "organizations/org-a"), { name: "School A", status: "active" });
    await setDoc(doc(db, "organizations/org-b"), { name: "School B", status: "active" });
    for (const [orgId, uid, role] of memberships) {
      const membership = { uid, role, status: "active", organizationId: orgId, organizationName: orgId };
      await setDoc(doc(db, `organizations/${orgId}/members/${uid}`), membership);
      await setDoc(doc(db, `userOrganizationMemberships/${uid}/organizations/${orgId}`), membership);
    }

    await setDoc(doc(db, "courses/course-a"), { organizationId: "org-a", name: "Course A" });
    await setDoc(doc(db, "courses/course-b"), { organizationId: "org-b", name: "Course B" });
    await setDoc(doc(db, "batches/batch-a"), { organizationId: "org-a", courseId: "course-a" });
    await setDoc(doc(db, "batches/batch-b"), { organizationId: "org-b", courseId: "course-b" });

    await setDoc(doc(db, "enrollments/enr-a"), {
      organizationId: "org-a", studentId: "student-a", instructorId: "teacher-a",
      batchId: "batch-a", status: "active"
    });
    await setDoc(doc(db, "enrollments/enr-a-other"), {
      organizationId: "org-a", studentId: "student-c", instructorId: "teacher-c",
      batchId: "batch-a", status: "active"
    });
    await setDoc(doc(db, "enrollments/enr-b"), {
      organizationId: "org-b", studentId: "student-b", instructorId: "teacher-b",
      batchId: "batch-b", status: "active"
    });
    await setDoc(doc(db, "payments/pay-a"), {
      organizationId: "org-a", studentId: "student-a", instructorId: "teacher-a",
      status: "pending", amount: 100000
    });
    await setDoc(doc(db, "attendance/att-a"), {
      organizationId: "org-a", studentId: "student-a", instructorId: "teacher-a",
      enrollmentId: "enr-a", batchId: "batch-a"
    });
    await setDoc(doc(db, "assessments/ass-a"), {
      organizationId: "org-a", studentId: "student-a", instructorId: "teacher-a",
      enrollmentId: "enr-a", batchId: "batch-a"
    });
  });
});

after(async () => { await env.cleanup(); });

test("user can list their own organization membership index", async () => {
  const db = env.authenticatedContext("student-a").firestore();
  const result = await assertSucceeds(getDocs(collection(db, "userOrganizationMemberships/student-a/organizations")));
  assert.equal(result.size, 1);
  assert.equal(result.docs[0].id, "org-a");
});

test("user cannot read another user's organization membership index", async () => {
  const db = env.authenticatedContext("student-a").firestore();
  await assertFails(getDoc(doc(db, "userOrganizationMemberships/student-b/organizations/org-b")));
});

test("student can read own enrollment inside their organization", async () => {
  const db = env.authenticatedContext("student-a").firestore();
  await assertSucceeds(getDoc(doc(db, "enrollments/enr-a")));
});

test("student cannot read another student's enrollment in the same organization", async () => {
  const db = env.authenticatedContext("student-a").firestore();
  await assertFails(getDoc(doc(db, "enrollments/enr-a-other")));
});

test("student cannot read another organization's course", async () => {
  const db = env.authenticatedContext("student-a").firestore();
  await assertFails(getDoc(doc(db, "courses/course-b")));
});

test("student can read their own organization's course", async () => {
  const db = env.authenticatedContext("student-a").firestore();
  await assertSucceeds(getDoc(doc(db, "courses/course-a")));
});

test("student cannot read another organization's batch", async () => {
  const db = env.authenticatedContext("student-a").firestore();
  await assertFails(getDoc(doc(db, "batches/batch-b")));
});

test("unaffiliated user cannot read organization or course data", async () => {
  const db = env.authenticatedContext("unaffiliated-user").firestore();
  await assertFails(getDoc(doc(db, "organizations/org-a")));
  await assertFails(getDoc(doc(db, "courses/course-a")));
});

test("organization admin can read their organization but not another school", async () => {
  const db = env.authenticatedContext("admin-a").firestore();
  await assertSucceeds(getDoc(doc(db, "organizations/org-a")));
  await assertFails(getDoc(doc(db, "organizations/org-b")));
  await assertSucceeds(getDoc(doc(db, "courses/course-a")));
  await assertFails(getDoc(doc(db, "courses/course-b")));
});

test("organization-scoped course query succeeds with an organizationId constraint", async () => {
  const db = env.authenticatedContext("student-a").firestore();
  const scoped = query(collection(db, "courses"), where("organizationId", "==", "org-a"));
  const result = await assertSucceeds(getDocs(scoped));
  assert.equal(result.size, 1);
});

test("unscoped cross-organization course query is denied", async () => {
  const db = env.authenticatedContext("student-a").firestore();
  await assertFails(getDocs(collection(db, "courses")));
});

test("finance role can read their organization's payment but not another school's data", async () => {
  const db = env.authenticatedContext("finance-a").firestore();
  await assertSucceeds(getDoc(doc(db, "payments/pay-a")));
  await assertFails(getDoc(doc(db, "enrollments/enr-b")));
});

test("student cannot write payment records directly", async () => {
  const db = env.authenticatedContext("student-a").firestore();
  await assertFails(setDoc(doc(db, "payments/forged"), {
    organizationId: "org-a", studentId: "student-a", amount: 300000
  }));
});

test("unauthenticated users cannot read organization data", async () => {
  const db = env.unauthenticatedContext().firestore();
  await assertFails(getDoc(doc(db, "courses/course-a")));
});

test("student cannot promote own role or edit membership", async () => {
  const db = env.authenticatedContext("student-a").firestore();
  await assertFails(setDoc(doc(db, "users/student-a"), {
    displayName: "Student", email: "student@example.com", role: "admin"
  }));
  await assertFails(setDoc(doc(db, "organizations/org-a/members/student-a"), {
    uid: "student-a", role: "admin", status: "active", organizationId: "org-a"
  }));
});

test("student cannot create enrollment directly", async () => {
  const db = env.authenticatedContext("student-a").firestore();
  await assertFails(setDoc(doc(db, "enrollments/forged"), {
    organizationId: "org-a", studentId: "student-a", batchId: "batch-a", status: "active"
  }));
});

test("instructor can read assigned enrollment inside their organization", async () => {
  const db = env.authenticatedContext("teacher-a").firestore();
  await assertSucceeds(getDoc(doc(db, "enrollments/enr-a")));
});

test("instructor cannot read enrollment assigned to another instructor", async () => {
  const db = env.authenticatedContext("teacher-a").firestore();
  await assertFails(getDoc(doc(db, "enrollments/enr-a-other")));
});

test("instructor cannot bypass audited attendance function", async () => {
  const db = env.authenticatedContext("teacher-a").firestore();
  await assertFails(setDoc(doc(db, "attendance/forged"), {
    organizationId: "org-a", enrollmentId: "enr-a", studentId: "student-a",
    instructorId: "teacher-a", batchId: "batch-a", sessionNo: 1,
    status: "present", markedBy: "teacher-a"
  }));
});

test("admin cannot write outcomes directly outside audited callable functions", async () => {
  const db = env.authenticatedContext("admin-a").firestore();
  await assertFails(setDoc(doc(db, "outcomes/forged"), {
    organizationId: "org-a", enrollmentId: "enr-a", studentId: "student-a", outcome: "completed"
  }));
});

test("inactive organization member loses all organization access", async () => {
  await env.withSecurityRulesDisabled(async (context) => {
    await setDoc(doc(context.firestore(), "organizations/org-a/members/student-a"), {
      uid: "student-a", role: "student", status: "suspended", organizationId: "org-a"
    });
  });
  const db = env.authenticatedContext("student-a").firestore();
  await assertFails(getDoc(doc(db, "courses/course-a")));
  await assertFails(getDoc(doc(db, "enrollments/enr-a")));
});
