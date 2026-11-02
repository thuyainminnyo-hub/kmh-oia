const test = require("node:test");
const assert = require("node:assert/strict");

const PROJECT_ID = process.env.GCLOUD_PROJECT || "demo-education-business-os";
const AUTH_HOST = process.env.FIREBASE_AUTH_EMULATOR_HOST || "127.0.0.1:9099";
const FIRESTORE_HOST = process.env.FIRESTORE_EMULATOR_HOST || "127.0.0.1:8080";
const FUNCTIONS_HOST = process.env.FUNCTIONS_EMULATOR_HOST || "127.0.0.1:5001";

// Explicitly keep this test isolated from production Firebase services.
process.env.GCLOUD_PROJECT = PROJECT_ID;
process.env.FIREBASE_AUTH_EMULATOR_HOST = AUTH_HOST;
process.env.FIRESTORE_EMULATOR_HOST = FIRESTORE_HOST;

const { initializeApp, deleteApp } = require("firebase-admin/app");
const { getAuth } = require("firebase-admin/auth");
const { getFirestore, FieldValue } = require("firebase-admin/firestore");

const app = initializeApp({ projectId: PROJECT_ID }, "aptivern-integration-" + process.pid);
const auth = getAuth(app);
const db = getFirestore(app);
const prefix = "it-" + process.pid + "-" + Date.now();

async function createAccount(role) {
  const email = role + "-" + prefix + "@example.test";
  const password = "Aptivern-Emulator-Only-Password-123!";
  const user = await auth.createUser({ email, password, displayName: "Integration " + role });
  await auth.setCustomUserClaims(user.uid, role === "platformAdmin" ? { platformAdmin: true } : { role });

  const response = await fetch(
    "http://" + AUTH_HOST + "/identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key=fake-api-key",
    {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ email, password, returnSecureToken: true })
    }
  );
  const body = await response.json();
  if (!response.ok || !body.idToken) {
    throw new Error("Auth emulator sign-in failed: " + JSON.stringify(body));
  }
  return { uid: user.uid, idToken: body.idToken };
}

async function callFunction(name, idToken, data) {
  const response = await fetch(
    "http://" + FUNCTIONS_HOST + "/" + PROJECT_ID + "/us-central1/" + name,
    {
      method: "POST",
      headers: {
        "content-type": "application/json",
        ...(idToken ? { authorization: "Bearer " + idToken } : {})
      },
      body: JSON.stringify({ data })
    }
  );
  const body = await response.json();
  if (!response.ok || body.error) {
    const error = new Error(body.error?.message || ("Callable function failed: " + response.status));
    error.code = body.error?.status;
    error.httpStatus = response.status;
    throw error;
  }
  return body.result;
}

function assertCallablePermissionDenied(error) {
  return error && error.code === "PERMISSION_DENIED";
}

async function getEnrollment(enrollmentId) {
  const snapshot = await db.collection("enrollments").doc(enrollmentId).get();
  assert.equal(snapshot.exists, true, "expected enrollment document to exist");
  return snapshot.data();
}

test("Aptivern callable enrollment/payment lifecycle works against Auth, Functions and Firestore emulators", async (t) => {
  const accounts = [];
  const batchIds = [];
  const enrollmentIds = [];
  const paymentIds = [];

  async function account(role) {
    const value = await createAccount(role);
    accounts.push(value);
    return value;
  }

  async function createBatch(fee) {
    const batchId = prefix + "-batch-" + batchIds.length;
    batchIds.push(batchId);
    await db.collection("batches").doc(batchId).set({
      organizationId: "aptivern",
      courseId: "aptivern__" + prefix + "-course",
      name: "Integration Test Batch",
      fee,
      currency: "MMK",
      status: "planned",
      createdAt: FieldValue.serverTimestamp()
    });
    return batchId;
  }

  async function createEnrollment(admin, student, fee) {
    const batchId = await createBatch(fee);
    const result = await callFunction("createEnrollment", admin.idToken, {
      organizationId: "aptivern",
      studentId: student.uid,
      batchId
    });
    enrollmentIds.push(result.enrollmentId);
    return { ...result, batchId };
  }

  async function recordPayment(actor, enrollmentId, amount) {
    const result = await callFunction("recordPayment", actor.idToken, {
      organizationId: "aptivern",
      enrollmentId,
      amount,
      method: "bank_transfer",
      reference: prefix + "-receipt-" + paymentIds.length
    });
    paymentIds.push(result.paymentId);
    return result;
  }

  t.after(async () => {
    for (const paymentId of paymentIds) {
      await db.collection("payments").doc(paymentId).delete().catch(() => {});
    }
    for (const enrollmentId of enrollmentIds) {
      await db.collection("enrollments").doc(enrollmentId).delete().catch(() => {});
      await db.collection("attendance").doc(enrollmentId + "_1").delete().catch(() => {});
      await db.collection("outcomes").doc(enrollmentId).delete().catch(() => {});
    }
    for (const batchId of batchIds) {
      await db.collection("batches").doc(batchId).delete().catch(() => {});
    }
    const audit = await db.collection("auditLogs").where("actorUid", "in", accounts.map(x => x.uid)).get().catch(() => null);
    if (audit) {
      const deletions = audit.docs.map(doc => doc.ref.delete());
      await Promise.all(deletions);
    }
    for (const organizationId of ["aptivern", prefix + "-school-b"]) {
      for (const user of accounts) {
        await db.collection("organizations").doc(organizationId).collection("members").doc(user.uid).delete().catch(() => {});
      }
      await db.collection("organizations").doc(organizationId).delete().catch(() => {});
    }
    for (const user of accounts) await auth.deleteUser(user.uid).catch(() => {});
    await deleteApp(app);
  });

  const admin = await account("admin");
  const student = await account("student");
  const platformAdmin = await account("platformAdmin");

  const organization = await callFunction("bootstrapOrganization", platformAdmin.idToken, {
    organizationId: "aptivern",
    name: "Aptivern Pilot"
  });
  assert.equal(organization.status, "active");
  await callFunction("setOrganizationMember", platformAdmin.idToken, {
    organizationId: "aptivern", uid: admin.uid, role: "admin"
  });
  await callFunction("setOrganizationMember", platformAdmin.idToken, {
    organizationId: "aptivern", uid: student.uid, role: "student"
  });

  const batchId = await createBatch(300000);

  let enrollment;
  let primaryEnrollmentId;
  await t.test("paid enrollment is pending until full verified payment", async () => {
    const created = await callFunction("createEnrollment", admin.idToken, {
      organizationId: "aptivern",
      studentId: student.uid,
      batchId
    });
    enrollmentIds.push(created.enrollmentId);
    enrollment = created;
    primaryEnrollmentId = created.enrollmentId;
    assert.equal(typeof primaryEnrollmentId, "string");
    assert.ok(primaryEnrollmentId.length > 0);
    assert.equal(created.status, "pending_payment");

    const state = await getEnrollment(created.enrollmentId);
    assert.equal(state.status, "pending_payment");
    assert.equal(state.feeAmount, 300000);
    assert.equal(state.paidAmount, 0);
    assert.equal(state.balanceDue, 300000);
  });

  await t.test("duplicate enrollment is rejected", async () => {
    await assert.rejects(
      callFunction("createEnrollment", admin.idToken, {
        organizationId: "aptivern",
        studentId: student.uid,
        batchId
      }),
      (error) => error && error.code === "ALREADY_EXISTS"
    );
  });

  let firstPayment;
  let secondPayment;
  await t.test("partial payments are reserved without activating enrollment", async () => {
    firstPayment = await recordPayment(admin, primaryEnrollmentId, 100000);
    secondPayment = await recordPayment(admin, primaryEnrollmentId, 200000);
    assert.ok(firstPayment.paymentId);
    assert.ok(secondPayment.paymentId);
    const state = await getEnrollment(primaryEnrollmentId);
    assert.equal(state.status, "pending_payment");
    assert.equal(state.pendingAmount, 300000);
    assert.equal(state.availableToSubmit, 0);
  });

  await t.test("student cannot record or verify payments through privileged functions", async () => {
    await assert.rejects(
      callFunction("recordPayment", student.idToken, {
        organizationId: "aptivern",
        enrollmentId: primaryEnrollmentId,
        amount: 100000,
        method: "cash"
      }),
      assertCallablePermissionDenied
    );
    await assert.rejects(
      callFunction("verifyPayment", student.idToken, {
        organizationId: "aptivern",
        paymentId: firstPayment.paymentId,
        verified: true
      }),
      assertCallablePermissionDenied
    );
  });

  await t.test("unauthenticated caller cannot verify payment", async () => {
    await assert.rejects(
      callFunction("verifyPayment", null, {
        organizationId: "aptivern",
        paymentId: firstPayment.paymentId,
        verified: true
      }),
      (error) => error && error.code === "UNAUTHENTICATED"
    );
  });

  await t.test("first verified installment leaves a balance and enrollment pending", async () => {
    const result = await callFunction("verifyPayment", admin.idToken, {
      organizationId: "aptivern",
      paymentId: firstPayment.paymentId,
      verified: true,
      note: "Synthetic emulator receipt verified"
    });
    assert.equal(result.status, "verified");
    assert.equal(result.enrollmentStatus, "pending_payment");
    const state = await getEnrollment(primaryEnrollmentId);
    assert.equal(state.paidAmount, 100000);
    assert.equal(state.pendingAmount, 200000);
    assert.equal(state.balanceDue, 200000);
    assert.equal(state.status, "pending_payment");
  });

  await t.test("final verified installment activates enrollment atomically", async () => {
    const result = await callFunction("verifyPayment", admin.idToken, {
      organizationId: "aptivern",
      paymentId: secondPayment.paymentId,
      verified: true,
      note: "Synthetic final installment verified"
    });
    assert.equal(result.status, "verified");
    assert.equal(result.enrollmentStatus, "active");
    const state = await getEnrollment(enrollment.enrollmentId);
    assert.equal(state.paidAmount, 300000);
    assert.equal(state.pendingAmount, 0);
    assert.equal(state.balanceDue, 0);
    assert.equal(state.status, "active");
    assert.ok(state.activatedAt);
  });

  await t.test("duplicate verification is rejected without changing the paid ledger", async () => {
    await assert.rejects(
      callFunction("verifyPayment", admin.idToken, {
        organizationId: "aptivern",
        paymentId: firstPayment.paymentId,
        verified: true
      }),
      (error) => error && error.code === "FAILED_PRECONDITION"
    );
    const state = await getEnrollment(enrollment.enrollmentId);
    assert.equal(state.paidAmount, 300000);
    assert.equal(state.status, "active");
  });

  await t.test("overpayment is rejected and rejected payment releases its reservation", async () => {
    const overpay = createBatch(300000);
    const overpayEnrollment = await callFunction("createEnrollment", admin.idToken, {
      organizationId: "aptivern",
      studentId: student.uid,
      batchId: await overpay
    });
    enrollmentIds.push(overpayEnrollment.enrollmentId);

    await assert.rejects(
      callFunction("recordPayment", admin.idToken, {
        organizationId: "aptivern",
        enrollmentId: overpayEnrollment.enrollmentId,
        amount: 300001,
        method: "cash"
      })
    );

    const rejectedPayment = await recordPayment(admin, overpayEnrollment.enrollmentId, 50000);
    const rejected = await callFunction("verifyPayment", admin.idToken, {
      organizationId: "aptivern",
      paymentId: rejectedPayment.paymentId,
      verified: false,
      note: "Synthetic test: receipt did not match"
    });
    assert.equal(rejected.status, "rejected");
    const state = await getEnrollment(overpayEnrollment.enrollmentId);
    assert.equal(state.paidAmount, 0);
    assert.equal(state.pendingAmount, 0);
    assert.equal(state.balanceDue, 300000);
    assert.equal(state.status, "pending_payment");
  });

  await t.test("zero-fee enrollment activates immediately", async () => {
    const freeBatch = await createBatch(0);
    const result = await callFunction("createEnrollment", admin.idToken, {
      organizationId: "aptivern",
      studentId: student.uid,
      batchId: freeBatch
    });
    enrollmentIds.push(result.enrollmentId);
    assert.equal(result.status, "active");
    const state = await getEnrollment(result.enrollmentId);
    assert.equal(state.feeAmount, 0);
    assert.equal(state.status, "active");
    assert.equal(state.balanceDue, 0);
  });

  await t.test("platform admin can bootstrap a separate organization and initial admin membership", async () => {
    const otherOrgId = prefix + "-school-b";
    const result = await callFunction("bootstrapOrganization", platformAdmin.idToken, {
      organizationId: otherOrgId,
      name: "Synthetic School B"
    });
    assert.equal(result.status, "active");
    const member = await db.collection("organizations").doc(otherOrgId)
      .collection("members").doc(platformAdmin.uid).get();
    assert.equal(member.exists, true);
    assert.equal(member.data().role, "admin");
    await db.collection("organizations").doc(otherOrgId).collection("members").doc(platformAdmin.uid).delete();
    await db.collection("organizations").doc(otherOrgId).delete();
  });

  await t.test("organization admin cannot use their membership to enroll in another organization", async () => {
    const otherOrgId = prefix + "-foreign-school";
    const foreignBatchId = prefix + "-foreign-batch";
    await db.collection("organizations").doc(otherOrgId).set({
      organizationId: otherOrgId, name: "Foreign School", status: "active"
    });
    await db.collection("batches").doc(foreignBatchId).set({
      organizationId: otherOrgId, courseId: otherOrgId + "__course",
      fee: 100000, currency: "MMK", status: "planned"
    });
    // Caller belongs to Aptivern, but attempts to reference a batch owned by School B.
    await assert.rejects(
      callFunction("createEnrollment", admin.idToken, {
        organizationId: "aptivern",
        studentId: student.uid,
        batchId: foreignBatchId
      }),
      (error) => error && error.code === "PERMISSION_DENIED"
    );

    const foreignEnrollmentId = prefix + "-foreign-enrollment";
    const foreignPaymentId = prefix + "-foreign-payment";
    await db.collection("enrollments").doc(foreignEnrollmentId).set({
      organizationId: otherOrgId, studentId: student.uid, batchId: foreignBatchId,
      feeAmount: 100000, paidAmount: 0, pendingAmount: 0, balanceDue: 100000,
      status: "pending_payment"
    });
    await db.collection("payments").doc(foreignPaymentId).set({
      organizationId: otherOrgId, enrollmentId: foreignEnrollmentId,
      studentId: student.uid, batchId: foreignBatchId, amount: 50000,
      currency: "MMK", method: "cash", status: "pending"
    });
    await assert.rejects(
      callFunction("recordPayment", admin.idToken, {
        organizationId: "aptivern", enrollmentId: foreignEnrollmentId,
        amount: 50000, method: "cash"
      }),
      (error) => error && error.code === "PERMISSION_DENIED"
    );
    await assert.rejects(
      callFunction("verifyPayment", admin.idToken, {
        organizationId: "aptivern", paymentId: foreignPaymentId, verified: true
      }),
      (error) => error && error.code === "PERMISSION_DENIED"
    );
    await db.collection("payments").doc(foreignPaymentId).delete();
    await db.collection("enrollments").doc(foreignEnrollmentId).delete();
    await db.collection("batches").doc(foreignBatchId).delete();
    await db.collection("organizations").doc(otherOrgId).delete();
  });

  await t.test("audit records exist for the payment lifecycle", async () => {
    const records = await db.collection("auditLogs")
      .where("enrollmentId", "==", enrollment.enrollmentId)
      .get();
    const actions = records.docs.map(doc => doc.data().action);
    assert.ok(actions.includes("payment.pending.created"));
    assert.ok(actions.includes("payment.verified"));
  });
});
