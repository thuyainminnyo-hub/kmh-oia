const test = require("node:test");
const assert = require("node:assert/strict");
const {
  initialPaymentState,
  reservePayment,
  settlePayment
} = require("../lib/payment-state.js");

test("free enrollment activates immediately with zero balance", () => {
  assert.deepEqual(initialPaymentState(0), {
    totalFee: 0,
    paidAmount: 0,
    pendingAmount: 0,
    status: "active",
    balanceDue: 0,
    availableToSubmit: 0
  });
});

test("paid enrollment starts pending payment", () => {
  assert.equal(initialPaymentState(300000).status, "pending_payment");
});

test("payment reservation cannot exceed remaining unreserved balance", () => {
  const reserved = reservePayment(300000, 0, 0, 100000);
  assert.equal(reserved.pendingAmount, 100000);
  assert.equal(reserved.balanceDue, 300000);
  assert.equal(reserved.availableToSubmit, 200000);
  assert.throws(() => reservePayment(300000, 0, 200000, 100001), /exceeds/);
});

test("partial verified payment leaves enrollment pending and updates balance", () => {
  const next = settlePayment(300000, 0, 100000, 100000, true);
  assert.equal(next.paidAmount, 100000);
  assert.equal(next.pendingAmount, 0);
  assert.equal(next.balanceDue, 200000);
  assert.equal(next.status, "pending_payment");
});

test("full verified payment activates enrollment", () => {
  const next = settlePayment(300000, 200000, 100000, 100000, true);
  assert.equal(next.paidAmount, 300000);
  assert.equal(next.pendingAmount, 0);
  assert.equal(next.balanceDue, 0);
  assert.equal(next.status, "active");
});

test("rejected payment releases reserved balance without increasing paid amount", () => {
  const next = settlePayment(300000, 50000, 100000, 100000, false);
  assert.equal(next.paidAmount, 50000);
  assert.equal(next.pendingAmount, 0);
  assert.equal(next.balanceDue, 250000);
  assert.equal(next.availableToSubmit, 250000);
  assert.equal(next.status, "pending_payment");
});

test("concurrent pending reservations are accounted for", () => {
  const first = reservePayment(300000, 0, 0, 100000);
  const second = reservePayment(300000, 0, first.pendingAmount, 150000);
  assert.equal(second.pendingAmount, 250000);
  assert.equal(second.availableToSubmit, 50000);
  assert.throws(() => reservePayment(300000, 0, second.pendingAmount, 50001), /exceeds/);
});

test("verification cannot settle more than the pending ledger", () => {
  assert.throws(() => settlePayment(300000, 0, 50000, 100000, true), /lower than the payment/);
});

test("settlement rejects an inconsistent paid and pending ledger", () => {
  assert.throws(() => settlePayment(300000, 250000, 100000, 100000, true), /exceed the course fee/);
});

test("invalid or unsafe currency values are rejected", () => {
  assert.throws(() => initialPaymentState(-1), /non-negative/);
  assert.throws(() => initialPaymentState(Number.MAX_SAFE_INTEGER + 1), /non-negative safe integer/);
  assert.throws(() => reservePayment(300000, 0, 0, 0), /positive/);
});
