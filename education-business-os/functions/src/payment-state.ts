export type EnrollmentStatus = "active" | "pending_payment";

export interface EnrollmentPaymentState {
  totalFee: number;
  paidAmount: number;
  pendingAmount: number;
  status: EnrollmentStatus;
  balanceDue: number;
  availableToSubmit: number;
}

function assertMoney(value: number, field: string): void {
  if (!Number.isSafeInteger(value) || value < 0) {
    throw new Error(field + " must be a non-negative safe integer.");
  }
}

export function initialPaymentState(totalFee: number): EnrollmentPaymentState {
  assertMoney(totalFee, "totalFee");
  return {
    totalFee,
    paidAmount: 0,
    pendingAmount: 0,
    status: totalFee === 0 ? "active" : "pending_payment",
    balanceDue: totalFee,
    availableToSubmit: totalFee
  };
}

export function reservePayment(
  totalFee: number,
  paidAmount: number,
  pendingAmount: number,
  amount: number
): Pick<EnrollmentPaymentState, "pendingAmount" | "status" | "balanceDue" | "availableToSubmit"> {
  assertMoney(totalFee, "totalFee");
  assertMoney(paidAmount, "paidAmount");
  assertMoney(pendingAmount, "pendingAmount");
  if (!Number.isSafeInteger(amount) || amount <= 0) {
    throw new Error("amount must be a positive safe integer.");
  }
  if (paidAmount + pendingAmount > totalFee) {
    throw new Error("Existing paid and pending amounts exceed the course fee.");
  }
  const available = totalFee - paidAmount - pendingAmount;
  if (amount > available) {
    throw new Error("Payment exceeds the remaining unreserved balance.");
  }
  const nextPending = pendingAmount + amount;
  return {
    pendingAmount: nextPending,
    status: paidAmount >= totalFee ? "active" : "pending_payment",
    balanceDue: totalFee - paidAmount,
    availableToSubmit: totalFee - paidAmount - nextPending
  };
}

export function settlePayment(
  totalFee: number,
  paidAmount: number,
  pendingAmount: number,
  amount: number,
  verified: boolean
): EnrollmentPaymentState {
  assertMoney(totalFee, "totalFee");
  assertMoney(paidAmount, "paidAmount");
  assertMoney(pendingAmount, "pendingAmount");
  if (!Number.isSafeInteger(amount) || amount <= 0) {
    throw new Error("amount must be a positive safe integer.");
  }
  if (typeof verified !== "boolean") {
    throw new Error("verified must be boolean.");
  }

  if (pendingAmount < amount) {
    throw new Error("Pending amount is lower than the payment being settled.");
  }
  const nextPaid = paidAmount + (verified ? amount : 0);
  if (nextPaid > totalFee) {
    throw new Error("Verification would overpay the course fee; manual reconciliation is required.");
  }
  const nextPending = Math.max(0, pendingAmount - amount);
  return {
    totalFee,
    paidAmount: nextPaid,
    pendingAmount: nextPending,
    status: nextPaid >= totalFee ? "active" : "pending_payment",
    balanceDue: totalFee - nextPaid,
    availableToSubmit: totalFee - nextPaid - nextPending
  };
}
