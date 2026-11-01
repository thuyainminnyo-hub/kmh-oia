import test from "node:test";
import assert from "node:assert/strict";
import { getCharacterById } from "../registry/index.mjs";
import { enforceCharacterLock, verifyProtectedIdentity } from "../registry/master-character-lock.mjs";

const thiri = await getCharacterById("MLCW-CHAR-001");

test("allows P01 outfit change while preserving canonical identity snapshot", () => {
  const result = enforceCharacterLock(thiri, { outfit: "P01" });
  assert.equal(result.registry_id, "MLCW-CHAR-001");
  assert.equal(result.approved_changes.outfit, "P01");
  assert.equal(result.qa_required, true);
  assert.equal(result.release_gate, "hold_until_visual_identity_and_boundary_qa_pass");
  assert.equal(Object.keys(result.protected_identity_snapshot).length, 7);
});

test("rejects direct changes to protected face and hair fields", () => {
  assert.throws(() => enforceCharacterLock(thiri, { face: "new-face" }), /rejected/);
  assert.throws(() => enforceCharacterLock(thiri, { hair: "new-hair" }), /rejected/);
});

test("rejects outfit IDs outside the registry", () => {
  assert.throws(() => enforceCharacterLock(thiri, { outfit: "P99" }), /Unknown outfit/);
});

test("rejects unknown mutation fields", () => {
  assert.throws(() => enforceCharacterLock(thiri, { age: 18 }), /rejected/);
});

test("protected identity comparison detects a changed face", () => {
  const before = { face: "canonical", hair: "bun" };
  const after = { face: "altered", hair: "bun" };
  const result = verifyProtectedIdentity(before, after);
  assert.equal(result.pass, false);
  assert.deepEqual(result.mismatches, ["face"]);
});

test("protected identity comparison passes unchanged attributes", () => {
  const state = { face: "same", eyes: "same", hair: "same" };
  assert.deepEqual(verifyProtectedIdentity(state, state), { pass: true, mismatches: [] });
});
