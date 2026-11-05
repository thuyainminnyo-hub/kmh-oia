import { readFile, readdir } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import path from "node:path";

const registryDir = fileURLToPath(new URL("./characters/", import.meta.url));

function assertCharacter(record, source) {
  const required = ["registry_id", "character_name", "registry_version", "identity_lock", "replaceable_attributes", "outfit_library"];
  for (const key of required) {
    if (!(key in record)) throw new Error(`Invalid character record ${source}: missing ${key}`);
  }
  if (!/^MLCW-CHAR-\d{3}$/.test(record.registry_id)) throw new Error(`Invalid character ID in ${source}`);
  if (!Array.isArray(record.outfit_library) || new Set(record.outfit_library).size !== record.outfit_library.length) {
    throw new Error(`Invalid or duplicate outfit IDs in ${source}`);
  }
  return record;
}

export async function listCharacters() {
  const files = (await readdir(registryDir)).filter((name) => name.endsWith(".json")).sort();
  const records = await Promise.all(files.map(async (name) => {
    const raw = await readFile(path.join(registryDir, name), "utf8");
    return assertCharacter(JSON.parse(raw), name);
  }));
  const ids = records.map((record) => record.registry_id);
  if (new Set(ids).size !== ids.length) throw new Error("Duplicate character registry IDs detected");
  return records;
}

export async function getCharacterById(characterId) {
  const records = await listCharacters();
  return records.find((record) => record.registry_id === characterId) ?? null;
}
