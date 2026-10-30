import { initializeApp } from "firebase-admin/app";
import { getAuth } from "firebase-admin/auth";
import { FieldValue, getFirestore } from "firebase-admin/firestore";
import { HttpsError, onCall } from "firebase-functions/v2/https";

initializeApp();
const db = getFirestore();

type CallableRequest = {
  auth?: { uid: string; token: Record<string, unknown> } | null;
  data?: Record<string, unknown>;
};

function requireRole(request: CallableRequest, allowed: string[]) {
  if (!request.auth) throw new HttpsError("unauthenticated", "Sign-in required.");
  const role = request.auth.token.role;
  if (typeof role !== "string" || !allowed.includes(role)) {
    throw new HttpsError("permission-denied", "Insufficient role.");
  }
  return { uid: request.auth.uid, role };
}

function requiredString(value: unknown, field: string, max = 120): string {
  if (typeof value !== "string" || value.trim().length === 0 || value.length > max) {
    throw new HttpsError("invalid-argument", field + " is required and must be at most " + max + " characters.");
  }
  return value.trim();
}

export const createEnrollment = onCall(async (request) => {
  const actor = requireRole(request, ["admin"]);
  const studentId = requiredString(request.data?.studentId, "studentId");
  const batchId = requiredString(request.data?.batchId, "batchId");
  const instructorId = request.data?.instructorId == null
    ? null : requiredString(request.data.instructorId, "instructorId");

  try { await getAuth().getUser(studentId); }
  catch { throw new HttpsError("not-found", "Student Auth user not found."); }
  const batchRef = db.collection("batches").doc(batchId);
  const enrollmentRef = db.collection("enrollments").doc();
  await db.runTransaction(async (tx) => {
    const batch = await tx.get(batchRef);
    if (!batch.exists) throw new HttpsError("not-found", "Batch not found.");
    const existing = await tx.get(db.collection("enrollments")
      .where("studentId", "==", studentId).where("batchId", "==", batchId));
    if (!existing.empty) throw new HttpsError("already-exists", "Student is already enrolled in this batch.");
    tx.create(enrollmentRef, {
      studentId, batchId, courseId: batch.data()!.courseId ?? "flutter-foundation",
      instructorId, status: "active", enrolledAt: FieldValue.serverTimestamp(),
      createdBy: actor.uid
    });
    tx.create(db.collection("auditLogs").doc(), {
      action: "enrollment.created", actorUid: actor.uid, targetId: enrollmentRef.id,
      createdAt: FieldValue.serverTimestamp()
    });
  });
  return { enrollmentId: enrollmentRef.id, status: "active" };
});

export const recordPayment = onCall(async (request) => {
  const actor = requireRole(request, ["admin", "instructor"]);
  const enrollmentId = requiredString(request.data?.enrollmentId, "enrollmentId");
  const amount = request.data?.amount;
  const method = request.data?.method;
  const reference = request.data?.reference;
  if (!Number.isInteger(amount) || (amount as number) <= 0 || (amount as number) > 100000000) {
    throw new HttpsError("invalid-argument", "Amount must be a positive integer in MMK.");
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
    if (actor.role === "instructor" && data.instructorId !== actor.uid) {
      throw new HttpsError("permission-denied", "Instructor is not assigned to this enrollment.");
    }
    tx.create(paymentRef, {
      enrollmentId, studentId: data.studentId, instructorId: data.instructorId ?? null,
      batchId: data.batchId, amount, currency: "MMK", method,
      reference: reference ?? null, status: "pending", recordedBy: actor.uid,
      createdAt: FieldValue.serverTimestamp()
    });
    tx.create(db.collection("auditLogs").doc(), {
      action: "payment.pending.created", actorUid: actor.uid, targetId: paymentRef.id,
      createdAt: FieldValue.serverTimestamp()
    });
  });
  return { paymentId: paymentRef.id, status: "pending" };
});

export const verifyPayment = onCall(async (request) => {
  const actor = requireRole(request, ["admin"]);
  const paymentId = requiredString(request.data?.paymentId, "paymentId");
  const verified = request.data?.verified;
  const note = request.data?.note;
  if (typeof verified !== "boolean") throw new HttpsError("invalid-argument", "verified must be boolean.");
  if (note !== undefined && (typeof note !== "string" || note.length > 500)) {
    throw new HttpsError("invalid-argument", "Note must be at most 500 characters.");
  }
  const ref = db.collection("payments").doc(paymentId);
  await db.runTransaction(async (tx) => {
    const snap = await tx.get(ref);
    if (!snap.exists) throw new HttpsError("not-found", "Payment not found.");
    if (snap.data()!.status !== "pending") {
      throw new HttpsError("failed-precondition", "Only pending payments can be verified.");
    }
    const status = verified ? "verified" : "rejected";
    tx.update(ref, {
      status, verifiedBy: actor.uid, verifiedAt: FieldValue.serverTimestamp(),
      verificationNote: note ?? null
    });
    tx.create(db.collection("auditLogs").doc(), {
      action: "payment." + status, actorUid: actor.uid, targetId: paymentId,
      createdAt: FieldValue.serverTimestamp()
    });
  });
  return { paymentId, status: verified ? "verified" : "rejected" };
});

export const markAttendance = onCall(async (request) => {
  const actor = requireRole(request, ["admin", "instructor"]);
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
    if (actor.role === "instructor" && data.instructorId !== actor.uid) {
      throw new HttpsError("permission-denied", "Instructor is not assigned to this enrollment.");
    }
    tx.set(attendanceRef, {
      enrollmentId, studentId: data.studentId, batchId: data.batchId,
      instructorId: data.instructorId ?? actor.uid, sessionNo, status,
      markedBy: actor.uid, markedAt: FieldValue.serverTimestamp()
    }, { merge: true });
    tx.create(db.collection("auditLogs").doc(), {
      action: "attendance." + status, actorUid: actor.uid, targetId: attendanceRef.id,
      createdAt: FieldValue.serverTimestamp()
    });
  });
  return { attendanceId: attendanceRef.id, status };
});

export const recordAssessment = onCall(async (request) => {
  const actor = requireRole(request, ["admin", "instructor"]);
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
    if (actor.role === "instructor" && data.instructorId !== actor.uid) {
      throw new HttpsError("permission-denied", "Instructor is not assigned to this enrollment.");
    }
    tx.set(assessmentRef, {
      enrollmentId, studentId: data.studentId, batchId: data.batchId,
      instructorId: data.instructorId ?? actor.uid, projectName, score, feedback,
      status: "reviewed", updatedBy: actor.uid, updatedAt: FieldValue.serverTimestamp()
    }, { merge: true });
    tx.create(db.collection("auditLogs").doc(), {
      action: "assessment.recorded", actorUid: actor.uid, targetId: assessmentRef.id,
      createdAt: FieldValue.serverTimestamp()
    });
  });
  return { assessmentId, score, status: "reviewed" };
});
