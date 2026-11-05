import test from "node:test";
import assert from "node:assert/strict";
import { getCharacterById, listCharacters } from "../registry/index.mjs";

test("retrieves Thiri by canonical Character ID", async () => {
  const thiri = await getCharacterById("MLCW-CHAR-001");
  assert.ok(thiri);
  assert.equal(thiri.character_name, "Thiri");
  assert.equal(thiri.registry_version, "1.0.0");
});

test("preserves identity lock and all ten outfit IDs", async () => {
  const thiri = await getCharacterById("MLCW-CHAR-001");
  assert.deepEqual(Object.keys(thiri.identity_lock).sort(), [
    "body_proportion", "earrings_and_accessories", "eyes", "face", "hair", "hair_ornament", "skin"
  ].sort());
  assert.deepEqual(thiri.outfit_library, ["P01","P02","P03","P04","P05","P06","P07","P08","P09","P10"]);
});

test("returns null for an unknown Character ID", async () => {
  assert.equal(await getCharacterById("MLCW-CHAR-999"), null);
});

test("registry has unique IDs", async () => {
  const records = await listCharacters();
  assert.equal(new Set(records.map((record) => record.registry_id)).size, records.length);
});
