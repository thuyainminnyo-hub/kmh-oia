#!/usr/bin/env python3
"""Validate KMH Prompt Library records against the repository JSON Schema.

Install dependency: python -m pip install jsonschema
Usage:
  python scripts/validate_prompt_record.py path/to/record.json
Exit 0 only when the record is schema-valid; this does not test prompt behavior,
approve the record, or prove production execution.
"""
import json
import sys
from pathlib import Path

try:
    from jsonschema import Draft202012Validator, FormatChecker
except ImportError:
    print("Missing dependency: install jsonschema (python -m pip install jsonschema)", file=sys.stderr)
    raise SystemExit(2)

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "schemas" / "prompt-library-record.schema.json"

def main() -> int:
    if len(sys.argv) != 2:
        print(f"Usage: {Path(sys.argv[0]).name} RECORD.json", file=sys.stderr)
        return 2
    try:
        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        record = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"Cannot read schema or record: {exc}", file=sys.stderr)
        return 2

    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    errors = sorted(validator.iter_errors(record), key=lambda err: list(map(str, err.absolute_path)))
    if errors:
        for err in errors:
            path = ".".join(map(str, err.absolute_path)) or "<root>"
            print(f"FAIL {path}: {err.message}")
        return 1
    print("PASS: record conforms to the Prompt Library record schema.")
    print("LIMIT: schema validation does not establish behavior, approval, or production execution.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
