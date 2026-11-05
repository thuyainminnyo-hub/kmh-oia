const PROTECTED_FIELDS = Object.freeze([
  "face", "eyes", "hair", "hair_ornament", "skin",
  "body_proportion", "earrings_and_accessories"
]);

const ALLOWED_CHANGE_FIELDS = new Set(["outfit", "pose", "scene", "background"]);

export function enforceCharacterLock(canonicalRecord, requestedChanges) {
  if (!canonicalRecord || canonicalRecord.record_status !== "draft" && canonicalRecord.record_status !== "active") {
    throw new Error("Canonical character record is missing or unavailable");
  }
  if (!requestedChanges || typeof requestedChanges !== "object" || Array.isArray(requestedChanges)) {
    throw new Error("Requested changes must be an object");
  }

  const protectedSnapshot = Object.fromEntries(
    PROTECTED_FIELDS.map((field) => [field, canonicalRecord.identity_lock[field]])
  );
  const rejected = Object.keys(requestedChanges).filter((field) => !ALLOWED_CHANGE_FIELDS.has(field));
  if (rejected.length) {
    throw new Error(`Identity lock rejected protected or unknown fields: ${rejected.join(", ")}`);
  }

  if (requestedChanges.outfit !== undefined) {
    if (!canonicalRecord.outfit_library.includes(requestedChanges.outfit)) {
      throw new Error(`Unknown outfit ID: ${requestedChanges.outfit}`);
    }
  }

  return Object.freeze({
    registry_id: canonicalRecord.registry_id,
    registry_version: canonicalRecord.registry_version,
    approved_changes: Object.freeze({ ...requestedChanges }),
    protected_identity_snapshot: Object.freeze(protectedSnapshot),
    qa_required: true,
    release_gate: "hold_until_visual_identity_and_boundary_qa_pass"
  });
}

export function verifyProtectedIdentity(before, after) {
  const mismatches = PROTECTED_FIELDS.filter((field) => {
    return JSON.stringify(before?.[field]) !== JSON.stringify(after?.[field]);
  });
  return { pass: mismatches.length === 0, mismatches };
}
