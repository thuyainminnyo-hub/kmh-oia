import { initializeApp } from "firebase-admin/app";
import { FieldValue, getFirestore } from "firebase-admin/firestore";
import { HttpsError, onCall } from "firebase-functions/v2/https";

initializeApp();
const db = getFirestore();

function requireRole(request: { auth?: { uid: string; token: Record<string, unknown> } | null }, allowed: string[]) {
  if (!request.auth) throw new HttpsError("unauthenticated", "Sign-in required.");
  const role = request.auth.token.role;
  if (typeof role !== "string" || !allowed.includes(role)) {
    throw new HttpsError("permission-denied", "Insufficient role.");
  }
  return request.auth.uid;
}

export const recordPayment = onCall(async (request) => {
  const actorUid = requireRole(request, ["admin", "instructor"]);
  const { enrollmentId, amount, method, reference } = request.data ?? {};
  if (typeof enrollmentId !== "string" || enrollmentId.length < 3 || enrollmentId.length > 120) {
    throw new HttpsError("invalid-argument", "Valid enrollmentId is required.");
  }
  if (!Number.isInteger(amount) || amount <= 0 || amount > 100000000) {
    throw new HttpsError("invalid-argument", "Amount must be a positive integer in MMK.");
  }
  if (!["cash", "bank_transfer", "other"].includes(method)) {
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
    if (request.auth!.token.role === "instructor" && data.instructorId !== actorUid) {
      throw new HttpsError("permission-denied", "Instructor is not assigned to this enrollment.");
    }
    tx.create(paymentRef, {
      enrollmentId, studentId: data.studentId, instructorId: data.instructorId ?? null,
      batchId: data.batchId, amount, currency: "MMK", method,
      reference: reference ?? null, status: "pending", recordedBy: actorUid,
      createdAt: FieldValue.serverTimestamp()
    });
    tx.create(db.collection("auditLogs").doc(), {
      action: "payment.pending.created", actorUid, targetId: paymentRef.id,
      createdAt: FieldValue.serverTimestamp()
    });
  });
  return { paymentId: paymentRef.id, status: "pending" };
});

export const verifyPayment = onCall(async (request) => {
  const actorUid = requireRole(request, ["admin"]);
  const { paymentId, verified, note } = request.data ?? {};
  if (typeof paymentId !== "string" || typeof verified !== "boolean") {
    throw new HttpsError("invalid-argument", "paymentId and verified are required.");
  }
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
      status, verifiedBy: actorUid, verifiedAt: FieldValue.serverTimestamp(),
      verificationNote: note ?? null
    });
    tx.create(db.collection("auditLogs").doc(), {
      action: "payment." + status, actorUid, targetId: paymentId,
      createdAt: FieldValue.serverTimestamp()
    });
  });
  return { paymentId, status: verified ? "verified" : "rejected" };
});
