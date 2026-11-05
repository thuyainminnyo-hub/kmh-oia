import { readFile } from "node:fs/promises";
import Ajv2020 from "ajv/dist/2020.js";
import { parseDocument } from "yaml";
import { getCharacterById } from "../registry/index.mjs";

const root = new URL("../", import.meta.url);
const read = (relative) => readFile(new URL(relative, root), "utf8");
const schema = JSON.parse(await read("registry/character.schema.json"));
const jsonRecord = JSON.parse(await read("registry/characters/thiri.json"));
const yamlDocument = parseDocument(await read("registry/characters/thiri.yaml"), { uniqueKeys: true });
if (yamlDocument.errors.length) throw new AggregateError(yamlDocument.errors, "YAML parse failed");
const yamlRecord = yamlDocument.toJS();

const ajv = new Ajv2020({ allErrors: true, strict: true });
const validate = ajv.compile(schema);
for (const [format, record] of [["JSON", jsonRecord], ["YAML", yamlRecord]]) {
  if (!validate(record)) {
    throw new Error(`${format} registry failed schema validation:\n${ajv.errorsText(validate.errors, { separator: "\n" })}`);
  }
}
if (JSON.stringify(jsonRecord) !== JSON.stringify(yamlRecord)) {
  throw new Error("JSON and YAML registry records are not semantically identical");
}
const retrieved = await getCharacterById("MLCW-CHAR-001");
if (!retrieved || retrieved.character_name !== "Thiri") {
  throw new Error("Runtime lookup failed for MLCW-CHAR-001");
}
console.log("PASS: JSON schema");
console.log("PASS: YAML parse + JSON Schema");
console.log("PASS: JSON/YAML semantic parity");
console.log("PASS: runtime lookup by MLCW-CHAR-001");
