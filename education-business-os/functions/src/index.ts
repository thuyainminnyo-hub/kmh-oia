import { createHash } from "node:crypto";
import { initializeApp } from "firebase-admin/app";
import { getAuth } from "firebase-admin/auth";
import { FieldValue, getFirestore } from "firebase-admin/firestore";
import { HttpsError, onCall } from "firebase-functions/v2/https";
import { initialPaymentState, reservePayment, settlePayment, type EnrollmentPaymentState } from "./payment-state";

initializeApp();
const db = getFirestore();

type CallableRequest = {
  auth?: { uid: string; token: Record<string, unknown> } | null;
  data?: Record<string, unknown>;
};

function requireRole(request: CallableRequest, allowed: string[]) {
  if (!request.auth) throw new HttpsError("unauthenticated", "Sign-in required.");
  const role = request.auth.token.platformAdmin === true ? "platformAdmin" : request.auth.token.role;
  if (typeof role !== "string" || !allowed.includes(role)) {
    throw new HttpsError("permission-denied", "Insufficient role.");
  }
  return { uid: request.auth.uid, role };
}

async function requireOrganizationRole(
  request: CallableRequest,
  organizationId: string,
  allowed: string[]
) {
  if (!request.auth) throw new HttpsError("unauthenticated", "Sign-in required.");
  if (request.auth.token.platformAdmin === true) {
    return { uid: request.auth.uid, role: "platformAdmin", organizationId };
  }
  const membership = await db.collection("organizations").doc(organizationId)
    .collection("members").doc(request.auth.uid).get();
  if (!membership.exists || membership.data()?.status !== "active") {
    throw new HttpsError("permission-denied", "Active organization membership required.");
  }
  const role = membership.data()?.role;
  if (typeof role !== "string" || !allowed.includes(role)) {
    throw new HttpsError("permission-denied", "Insufficient organization role.");
  }
  return { uid: request.auth.uid, role, organizationId };
}

function requiredString(value: unknown, field: string, max = 120): string {
  if (typeof value !== "string" || value.trim().length === 0 || value.length > max) {
    throw new HttpsError("invalid-argument", field + " is required and must be at most " + max + " characters.");
  }
  return value.trim();
}

function requiredOrganizationId(value: unknown): string {
  const organizationId = requiredString(value, "organizationId", 80);
  if (
    organizationId === "." ||
    organizationId === ".." ||
    organizationId.includes("/") ||
    organizationId.includes(String.fromCharCode(92))
  ) {
    throw new HttpsError("invalid-argument", "organizationId must be a single safe document ID.");
  }
  return organizationId;
}

export const bootstrapOrganization = onCall(async (request) => {
  const actor = requireRole(request, ["platformAdmin"]);
  const organizationId = requiredOrganizationId(request.data?.organizationId);
  const name = requiredString(request.data?.name, "name", 160);
  const organizationRef = db.collection("organizations").doc(organizationId);
  const memberRef = organizationRef.collection("members").doc(actor.uid);
  const userMembershipRef = db.collection("userOrganizationMemberships").doc(actor.uid)
    .collection("organizations").doc(organizationId);
  await db.runTransaction(async (tx) => {
    const existing = await tx.get(organizationRef);
    if (existing.exists) throw new HttpsError("already-exists", "Organization ID already exists.");
    tx.create(organizationRef, {
      organizationId, name, status: "active",
      createdBy: actor.uid, createdAt: FieldValue.serverTimestamp()
    });
    const membership = {
      organizationId, uid: actor.uid, role: "admin", status: "active",
      organizationName: name, createdBy: actor.uid, createdAt: FieldValue.serverTimestamp()
    };
    tx.create(memberRef, membership);
    tx.create(userMembershipRef, membership);
    tx.create(db.collection("auditLogs").doc(), {
      organizationId, action: "organization.created", actorUid: actor.uid,
      targetId: organizationId, createdAt: FieldValue.serverTimestamp()
    });
  });
  return { organizationId, name, ownerUid: actor.uid, status: "active" };
});

export const setOrganizationMember = onCall(async (request) => {
  const organizationId = requiredOrganizationId(request.data?.organizationId);
  const actor = await requireOrganizationRole(request, organizationId, ["admin"]);
  const uid = requiredString(request.data?.uid, "uid");
  const role = request.data?.role;
  const allowedRoles = ["admin", "academic_manager", "instructor", "finance", "student", "creator", "moderator"];
  if (typeof role !== "string" || !allowedRoles.includes(role)) {
    throw new HttpsError("invalid-argument", "Unsupported organization role.");
  }
  const status = request.data?.status ?? "active";
  if (status !== "active" && status !== "suspended") {
    throw new HttpsError("invalid-argument", "Membership status must be active or suspended.");
  }
  try { await getAuth().getUser(uid); }
  catch { throw new HttpsError("not-found", "Firebase Auth user not found."); }

  const memberRef = db.collection("organizations").doc(organizationId).collection("members").doc(uid);
  const userMembershipRef = db.collection("userOrganizationMemberships").doc(uid)
    .collection("organizations").doc(organizationId);
  await db.runTransaction(async (tx) => {
    const organizationRef = db.collection("organizations").doc(organizationId);
    const organization = await tx.get(organizationRef);
    if (!organization.exists || organization.data()?.status !== "active") {
      throw new HttpsError("not-found", "Active organization not found.");
    }
    const [existingMember, activeAdmins] = await Promise.all([
      tx.get(memberRef),
      tx.get(db.collection("organizations").doc(organizationId).collection("members")
        .where("role", "==", "admin").where("status", "==", "active"))
    ]);
    const isRemovingAdmin = existingMember.exists &&
      existingMember.data()?.role === "admin" &&
      (role !== "admin" || status !== "active");
    if (isRemovingAdmin && activeAdmins.size <= 1) {
      throw new HttpsError("failed-precondition", "Cannot demote or suspend the last active organization admin. Promote another admin first.");
    }
    const membership = {
      organizationId, uid, role, status,
      organizationName: organization.data()?.name ?? organizationId,
      updatedBy: actor.uid, updatedAt: FieldValue.serverTimestamp()
    };
    tx.set(memberRef, membership, { merge: true });
    tx.set(userMembershipRef, membership, { merge: true });
    tx.create(db.collection("auditLogs").doc(), {
      organizationId, action: "organization.member.updated",
      actorUid: actor.uid, targetId: uid, role, status,
      createdAt: FieldValue.serverTimestamp()
    });
  });
  return { organizationId, uid, role, status };
});

export const createEnrollment = onCall(async (request) => {
  const organizationId = requiredOrganizationId(request.data?.organizationId);
  const actor = await requireOrganizationRole(request, organizationId, ["admin"]);
  const studentId = requiredString(request.data?.studentId, "studentId");
  const batchId = requiredString(request.data?.batchId, "batchId");
  const instructorId = request.data?.instructorId == null
    ? null : requiredString(request.data.instructorId, "instructorId");

  try { await getAuth().getUser(studentId); }
  catch { throw new HttpsError("not-found", "Student Auth user not found."); }
  const batchRef = db.collection("batches").doc(batchId);
  const enrollmentId = createHash("sha256")
    .update(organizationId + ":" + studentId + ":" + batchId)
    .digest("hex");
  const enrollmentRef = db.collection("enrollments").doc(enrollmentId);
  const studentMembershipRef = db.collection("organizations").doc(organizationId).collection("members").doc(studentId);
  const instructorMembershipRef = instructorId
    ? db.collection("organizations").doc(organizationId).collection("members").doc(instructorId)
    : null;

  if (instructorId) {
    try { await getAuth().getUser(instructorId); }
    catch { throw new HttpsError("not-found", "Instructor Auth user not found."); }
  }

  const createdStatus = await db.runTransaction(async (tx) => {
    const batch = await tx.get(batchRef);
    const studentMembership = await tx.get(studentMembershipRef);
    const instructorMembership = instructorMembershipRef ? await tx.get(instructorMembershipRef) : null;
    const existing = await tx.get(enrollmentRef);
    if (!batch.exists) throw new HttpsError("not-found", "Batch not found.");
    if (!existing.exists && (!studentMembership.exists ||
        studentMembership.data()?.status !== "active" ||
        studentMembership.data()?.role !== "student")) {
      throw new HttpsError("failed-precondition", "Student must have an active membership in this organization.");
    }
    if (existing.exists) {
      throw new HttpsError("already-exists", "Student is already enrolled in this batch.");
    }
    if (instructorId && (!instructorMembership?.exists ||
        instructorMembership.data()?.status !== "active" ||
        instructorMembership.data()?.role !== "instructor")) {
      throw new HttpsError("failed-precondition", "Instructor must have an active instructor membership in this organization.");
    }
    const batchData = batch.data()!;
    if (batchData.organizationId !== organizationId) {
      throw new HttpsError("permission-denied", "Batch belongs to another organization.");
    }
    const fee = batchData.fee;
    if (!Number.isSafeInteger(fee) || (fee as number) < 0) {
      throw new HttpsError("failed-precondition", "Batch fee must be a non-negative integer before enrollment.");
    }
    const currency = typeof batchData.currency === "string" ? batchData.currency : "MMK";
    if (currency !== "MMK") throw new HttpsError("failed-precondition", "Pilot currently supports MMK enrollment fees only.");
    const paymentState = initialPaymentState(fee as number);
    tx.create(enrollmentRef, {
      organizationId, studentId, batchId,
      courseId: batchData.courseId ?? "flutter-foundation",
      instructorId,
      feeAmount: paymentState.totalFee,
      currency,
      paidAmount: paymentState.paidAmount,
      pendingAmount: paymentState.pendingAmount,
      balanceDue: paymentState.balanceDue,
      status: paymentState.status,
      enrolledAt: FieldValue.serverTimestamp(),
      ...(paymentState.status === "active" ? { activatedAt: FieldValue.serverTimestamp() } : {}),
      createdBy: actor.uid
    });
    tx.create(db.collection("auditLogs").doc(), {
      organizationId,
      action: paymentState.status === "active" ? "enrollment.created_free" : "enrollment.created_pending_payment",
      actorUid: actor.uid,
      targetId: enrollmentRef.id,
      feeAmount: paymentState.totalFee,
      currency,
      createdAt: FieldValue.serverTimestamp()
    });
    return paymentState.status;
  });
  return { enrollmentId: enrollmentRef.id, status: createdStatus };
});

export const recordPayment = onCall(async (request) => {
  const organizationId = requiredOrganizationId(request.data?.organizationId);
  const actor = await requireOrganizationRole(request, organizationId, ["admin", "instructor", "finance"]);
  const enrollmentId = requiredString(request.data?.enrollmentId, "enrollmentId");
  const amount = request.data?.amount;
  const method = request.data?.method;
  const reference = request.data?.reference;
  if (!Number.isSafeInteger(amount) || (amount as number) <= 0 || (amount as number) > 100000000) {
    throw new HttpsError("invalid-argument", "Amount must be a positive safe integer in MMK.");
  }
  if (!["cash", "bank_transfer", "other"].includes(String(method))) {
    throw new HttpsError("invalid-argument", "Unsupported payment method.");
  }
  if (reference !== undefined && (typeof reference !== "string" || reference.length > 120)) {
    throw new HttpsError("invalid-argument", "Reference is too long.");
  }

  const enrollmentRef = db.collection("enrollments").doc(enrollmentId);
  const paymentRef = db.collection("payments").doc();
  await db.runTransaction(async (tx) => {
    const enrollment = await tx.get(enrollmentRef);
    if (!enrollment.exists) throw new HttpsError("not-found", "Enrollment not found.");
    const data = enrollment.data()!;
    if (data.organizationId !== organizationId) {
      throw new HttpsError("permission-denied", "Enrollment belongs to another organization.");
    }
    if (actor.role === "instructor" && data.instructorId !== actor.uid) {
      throw new HttpsError("permission-denied", "Instructor is not assigned to this enrollment.");
    }
    if (data.status === "cancelled" || data.status === "withdrawn" || data.status === "suspended") {
      throw new HttpsError("failed-precondition", "Payment cannot be recorded for this enrollment status.");
    }
    const batchRef = db.collection("batches").doc(String(data.batchId));
    const batch = typeof data.feeAmount === "number" ? null : await tx.get(batchRef);
    if (batch && batch.data()?.organizationId !== organizationId) {
      throw new HttpsError("permission-denied", "Batch belongs to another organization.");
    }
    const feeAmount = typeof data.feeAmount === "number" ? data.feeAmount : batch?.data()?.fee;
    if (!Number.isSafeInteger(feeAmount) || (feeAmount as number) < 0) {
      throw new HttpsError("failed-precondition", "Enrollment has no valid course fee; reconcile this enrollment first.");
    }
    const paidAmount = typeof data.paidAmount === "number" ? data.paidAmount : 0;
    const pendingAmount = typeof data.pendingAmount === "number" ? data.pendingAmount : 0;
    let reserved: ReturnType<typeof reservePayment>;
    try {
      reserved = reservePayment(feeAmount as number, paidAmount, pendingAmount, amount as number);
    } catch (error) {
      throw new HttpsError("failed-precondition", error instanceof Error ? error.message : "Payment amount is invalid.");
    }
    const currency = data.currency ?? batch?.data()?.currency ?? "MMK";
    tx.update(enrollmentRef, {
      feeAmount, currency,
      pendingAmount: reserved.pendingAmount,
      balanceDue: reserved.balanceDue,
      availableToSubmit: reserved.availableToSubmit,
      updatedAt: FieldValue.serverTimestamp()
    });
    tx.create(paymentRef, {
      organizationId, enrollmentId,
      studentId: data.studentId,
      instructorId: data.instructorId ?? null,
      batchId: data.batchId,
      amount, currency, method,
      reference: reference ?? null,
      status: "pending",
      recordedBy: actor.uid,
      createdAt: FieldValue.serverTimestamp()
    });
    tx.create(db.collection("auditLogs").doc(), {
      organizationId,
      action: "payment.pending.created",
      actorUid: actor.uid,
      targetId: paymentRef.id,
      enrollmentId,
      amount,
      createdAt: FieldValue.serverTimestamp()
    });
  });
  return { paymentId: paymentRef.id, status: "pending" };
});

export const verifyPayment = onCall(async (request) => {
  const organizationId = requiredOrganizationId(request.data?.organizationId);
  const actor = await requireOrganizationRole(request, organizationId, ["admin", "finance"]);
  const paymentId = requiredString(request.data?.paymentId, "paymentId");
  const verified = request.data?.verified;
  const note = request.data?.note;
  if (typeof verified !== "boolean") throw new HttpsError("invalid-argument", "verified must be boolean.");
  if (note !== undefined && (typeof note !== "string" || note.length > 500)) {
    throw new HttpsError("invalid-argument", "Note must be at most 500 characters.");
  }

  const paymentRef = db.collection("payments").doc(paymentId);
  const resultingEnrollmentStatus = await db.runTransaction(async (tx) => {
    const payment = await tx.get(paymentRef);
    if (!payment.exists) throw new HttpsError("not-found", "Payment not found.");
    const paymentData = payment.data()!;
    if (paymentData.organizationId !== organizationId) {
      throw new HttpsError("permission-denied", "Payment belongs to another organization.");
    }
    if (paymentData.status !== "pending") {
      throw new HttpsError("failed-precondition", "Only pending payments can be verified.");
    }
    const enrollmentRef = db.collection("enrollments").doc(String(paymentData.enrollmentId));
    const enrollment = await tx.get(enrollmentRef);
    if (!enrollment.exists) throw new HttpsError("not-found", "Related enrollment not found.");
    const enrollmentData = enrollment.data()!;
    if (enrollmentData.organizationId !== organizationId) {
      throw new HttpsError("permission-denied", "Enrollment belongs to another organization.");
    }
    const batchRef = db.collection("batches").doc(String(enrollmentData.batchId));
    const batch = typeof enrollmentData.feeAmount === "number" ? null : await tx.get(batchRef);
    if (batch && batch.data()?.organizationId !== organizationId) {
      throw new HttpsError("permission-denied", "Batch belongs to another organization.");
    }
    const feeAmount = typeof enrollmentData.feeAmount === "number" ? enrollmentData.feeAmount : batch?.data()?.fee;
    if (!Number.isSafeInteger(feeAmount) || (feeAmount as number) < 0) {
      throw new HttpsError("failed-precondition", "Enrollment has no valid course fee; reconcile this enrollment first.");
    }
    const paidAmount = typeof enrollmentData.paidAmount === "number" ? enrollmentData.paidAmount : 0;
    const pendingAmount = typeof enrollmentData.pendingAmount === "number" ? enrollmentData.pendingAmount : 0;
    if (!Number.isSafeInteger(paymentData.amount) || paymentData.amount <= 0) {
      throw new HttpsError("failed-precondition", "Payment record has an invalid amount.");
    }
    let nextState: EnrollmentPaymentState;
    try {
      nextState = settlePayment(feeAmount as number, paidAmount, pendingAmount, paymentData.amount, verified);
    } catch (error) {
      throw new HttpsError("failed-precondition", error instanceof Error ? error.message : "Payment settlement failed.");
    }
    const nextPaymentStatus = verified ? "verified" : "rejected";
    const wasActive = enrollmentData.status === "active";
    tx.update(paymentRef, {
      status: nextPaymentStatus,
      reviewedBy: actor.uid,
      reviewedAt: FieldValue.serverTimestamp(),
      verificationNote: note ?? null
    });
    tx.update(enrollmentRef, {
      feeAmount: nextState.totalFee,
      paidAmount: nextState.paidAmount,
      pendingAmount: nextState.pendingAmount,
      balanceDue: nextState.balanceDue,
      availableToSubmit: nextState.availableToSubmit,
      status: nextState.status,
      updatedAt: FieldValue.serverTimestamp(),
      ...(nextState.status === "active" && !wasActive ? { activatedAt: FieldValue.serverTimestamp() } : {})
    });
    tx.create(db.collection("auditLogs").doc(), {
      organizationId,
      action: "payment." + nextPaymentStatus,
      actorUid: actor.uid,
      targetId: paymentId,
      enrollmentId: enrollmentRef.id,
      amount: paymentData.amount,
      enrollmentStatus: nextState.status,
      createdAt: FieldValue.serverTimestamp()
    });
    return nextState.status;
  });
  return { paymentId, status: verified ? "verified" : "rejected", enrollmentStatus: resultingEnrollmentStatus };
});

export const markAttendance = onCall(async (request) => {
  const organizationId = requiredOrganizationId(request.data?.organizationId);
  const actor = await requireOrganizationRole(request, organizationId, ["admin", "instructor", "academic_manager"]);
  const enrollmentId = requiredString(request.data?.enrollmentId, "enrollmentId");
  const sessionNo = request.data?.sessionNo;
  const status = request.data?.status;
  if (!Number.isInteger(sessionNo) || (sessionNo as number) < 1 || (sessionNo as number) > 24) {
    throw new HttpsError("invalid-argument", "sessionNo must be between 1 and 24.");
  }
  if (!["present", "absent", "late", "excused"].includes(String(status))) {
    throw new HttpsError("invalid-argument", "Unsupported attendance status.");
  }
  const enrollmentRef = db.collection("enrollments").doc(enrollmentId);
  const attendanceRef = db.collection("attendance").doc(enrollmentId + "_" + sessionNo);
  await db.runTransaction(async (tx) => {
    const enrollment = await tx.get(enrollmentRef);
    if (!enrollment.exists) throw new HttpsError("not-found", "Enrollment not found.");
    const data = enrollment.data()!;
    if (data.organizationId !== organizationId) throw new HttpsError("permission-denied", "Enrollment belongs to another organization.");
    if (actor.role === "instructor" && data.instructorId !== actor.uid) {
      throw new HttpsError("permission-denied", "Instructor is not assigned to this enrollment.");
    }
    tx.set(attendanceRef, {
      organizationId, enrollmentId, studentId: data.studentId, batchId: data.batchId,
      instructorId: data.instructorId ?? actor.uid, sessionNo, status,
      markedBy: actor.uid, markedAt: FieldValue.serverTimestamp()
    }, { merge: true });
    tx.create(db.collection("auditLogs").doc(), {
      organizationId, action: "attendance." + status, actorUid: actor.uid,
      targetId: attendanceRef.id, createdAt: FieldValue.serverTimestamp()
    });
  });
  return { attendanceId: attendanceRef.id, status };
});

export const recordAssessment = onCall(async (request) => {
  const organizationId = requiredOrganizationId(request.data?.organizationId);
  const actor = await requireOrganizationRole(request, organizationId, ["admin", "instructor", "academic_manager"]);
  const enrollmentId = requiredString(request.data?.enrollmentId, "enrollmentId");
  const projectName = requiredString(request.data?.projectName, "projectName", 100);
  const score = request.data?.score;
  const feedback = request.data?.feedback ?? "";
  if (typeof score !== "number" || !Number.isFinite(score) || score < 0 || score > 100) {
    throw new HttpsError("invalid-argument", "Score must be between 0 and 100.");
  }
  if (typeof feedback !== "string" || feedback.length > 2000) {
    throw new HttpsError("invalid-argument", "Feedback must be at most 2000 characters.");
  }
  const enrollmentRef = db.collection("enrollments").doc(enrollmentId);
  const assessmentId = enrollmentId + "_" + projectName.toLowerCase().replace(/[^a-z0-9]+/g, "-").slice(0, 40);
  const assessmentRef = db.collection("assessments").doc(assessmentId);
  await db.runTransaction(async (tx) => {
    const enrollment = await tx.get(enrollmentRef);
    if (!enrollment.exists) throw new HttpsError("not-found", "Enrollment not found.");
    const data = enrollment.data()!;
    if (data.organizationId !== organizationId) throw new HttpsError("permission-denied", "Enrollment belongs to another organization.");
    if (actor.role === "instructor" && data.instructorId !== actor.uid) {
      throw new HttpsError("permission-denied", "Instructor is not assigned to this enrollment.");
    }
    tx.set(assessmentRef, {
      organizationId, enrollmentId, studentId: data.studentId, batchId: data.batchId,
      instructorId: data.instructorId ?? actor.uid, projectName, score, feedback,
      status: "reviewed", updatedBy: actor.uid, updatedAt: FieldValue.serverTimestamp()
    }, { merge: true });
    tx.create(db.collection("auditLogs").doc(), {
      organizationId, action: "assessment.recorded", actorUid: actor.uid,
      targetId: assessmentRef.id, createdAt: FieldValue.serverTimestamp()
    });
  });
  return { assessmentId, score, status: "reviewed" };
});

/**
 * Admin-managed role assignment. Bootstrap the first admin out-of-band with
 * a trusted Firebase Admin SDK session; never expose service-account keys.
 */
export const setUserRole = onCall(async (request) => {
  const actor = requireRole(request, ["platformAdmin"]);
  const uid = requiredString(request.data?.uid, "uid");
  const role = request.data?.role;
  if (!["admin", "instructor", "student"].includes(String(role))) {
    throw new HttpsError("invalid-argument", "Role must be admin, instructor or student.");
  }
  try {
    const user = await getAuth().getUser(uid);
    await getAuth().setCustomUserClaims(uid, { ...(user.customClaims ?? {}), role });
  } catch (error) {
    if (error instanceof HttpsError) throw error;
    throw new HttpsError("not-found", "Firebase Auth user not found.");
  }
  await db.collection("auditLogs").add({
    action: "user.role.updated", actorUid: actor.uid, targetId: uid,
    role, createdAt: FieldValue.serverTimestamp()
  });
  return { uid, role, message: "Role updated. User must refresh their ID token." };
});


export const createCourseBatch = onCall(async (request) => {
  const organizationId = requiredOrganizationId(request.data?.organizationId);
  const actor = await requireOrganizationRole(request, organizationId, ["admin"]);
  const courseIdInput = requiredString(request.data?.courseId, "courseId", 80);
  const courseName = requiredString(request.data?.courseName, "courseName", 120);
  const batchId = requiredString(request.data?.batchId, "batchId", 80);
  const startDate = requiredString(request.data?.startDate, "startDate", 10);
  const fee = request.data?.fee;
  const currency = request.data?.currency ?? "MMK";
  const schedule = request.data?.schedule;
  if (!/^\d{4}-\d{2}-\d{2}$/.test(startDate)) {
    throw new HttpsError("invalid-argument", "startDate must use YYYY-MM-DD.");
  }
  if (!Number.isSafeInteger(fee) || (fee as number) < 0 || (fee as number) > 100000000) {
    throw new HttpsError("invalid-argument", "fee must be a non-negative safe integer.");
  }
  if (currency !== "MMK") throw new HttpsError("invalid-argument", "Pilot currently supports MMK only.");
  if (!Array.isArray(schedule) || schedule.length === 0 || schedule.length > 7 ||
      schedule.some((day) => typeof day !== "string" || !["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"].includes(day))) {
    throw new HttpsError("invalid-argument", "schedule must contain valid weekday names.");
  }
  // Prefix course IDs with tenant ID to prevent cross-organization document collisions.
  const courseId = organizationId + "__" + courseIdInput;
  const courseRef = db.collection("courses").doc(courseId);
  const batchRef = db.collection("batches").doc(batchId);
  await db.runTransaction(async (tx) => {
    const existing = await tx.get(batchRef);
    if (existing.exists) throw new HttpsError("already-exists", "Batch ID already exists.");
    const course = await tx.get(courseRef);
    if (course.exists && course.data()?.organizationId !== organizationId) {
      throw new HttpsError("permission-denied", "Course ID collision across organizations.");
    }
    tx.set(courseRef, {
      organizationId, name: courseName,
      updatedAt: FieldValue.serverTimestamp(), updatedBy: actor.uid
    }, { merge: true });
    tx.create(batchRef, {
      organizationId, courseId, name: courseName, startDate, fee, currency,
      schedule, status: "planned", createdAt: FieldValue.serverTimestamp(),
      createdBy: actor.uid
    });
    tx.create(db.collection("auditLogs").doc(), {
      organizationId, action: "course.batch.created", actorUid: actor.uid,
      targetId: batchId, createdAt: FieldValue.serverTimestamp()
    });
  });
  return { organizationId, courseId, batchId, status: "planned" };
});

export const recordOutcome = onCall(async (request) => {
  const organizationId = requiredOrganizationId(request.data?.organizationId);
  const actor = await requireOrganizationRole(request, organizationId, ["admin", "instructor", "academic_manager"]);
  const enrollmentId = requiredString(request.data?.enrollmentId, "enrollmentId");
  const outcome = request.data?.outcome;
  const evidence = request.data?.evidence ?? "";
  if (!["completed", "not_completed", "withdrawn"].includes(String(outcome))) {
    throw new HttpsError("invalid-argument", "Unsupported outcome.");
  }
  if (typeof evidence !== "string" || evidence.length > 1000) {
    throw new HttpsError("invalid-argument", "Evidence note must be at most 1000 characters.");
  }
  const enrollmentRef = db.collection("enrollments").doc(enrollmentId);
  const outcomeRef = db.collection("outcomes").doc(enrollmentId);
  await db.runTransaction(async (tx) => {
    const enrollment = await tx.get(enrollmentRef);
    if (!enrollment.exists) throw new HttpsError("not-found", "Enrollment not found.");
    const data = enrollment.data()!;
    if (data.organizationId !== organizationId) throw new HttpsError("permission-denied", "Enrollment belongs to another organization.");
    if (actor.role === "instructor" && data.instructorId !== actor.uid) {
      throw new HttpsError("permission-denied", "Instructor is not assigned to this enrollment.");
    }
    tx.set(outcomeRef, {
      organizationId, enrollmentId, studentId: data.studentId, batchId: data.batchId,
      instructorId: data.instructorId ?? actor.uid, outcome, evidence,
      recordedBy: actor.uid, recordedAt: FieldValue.serverTimestamp()
    }, { merge: true });
    tx.update(enrollmentRef, { status: outcome === "completed" ? "completed" : outcome });
    tx.create(db.collection("auditLogs").doc(), {
      organizationId, action: "student.outcome.recorded", actorUid: actor.uid,
      targetId: enrollmentId, outcome, createdAt: FieldValue.serverTimestamp()
    });
  });
  return { organizationId, enrollmentId, outcome };
});

