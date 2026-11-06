#!/usr/bin/env python3
"""Validate a KMH OIA cybersecurity record against its JSON Schema."""
import json
import sys
from pathlib import Path

try:
    from jsonschema import Draft202012Validator, FormatChecker
except ImportError:
    print("Missing dependency: install jsonschema.", file=sys.stderr)
    raise SystemExit(2)

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "schemas" / "cybersecurity-threat-record.schema.json"

def main():
    if len(sys.argv) != 2:
        print("Usage: python scripts/validate_cybersecurity_record.py RECORD.json", file=sys.stderr)
        return 2
    try:
        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        record = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print("Input error: {}".format(exc), file=sys.stderr)
        return 2
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    errors = sorted(validator.iter_errors(record), key=lambda err: list(map(str, err.absolute_path)))
    if errors:
        for error in errors:
            path = ".".join(map(str, error.absolute_path)) or "<root>"
            print("INVALID {}: {}".format(path, error.message), file=sys.stderr)
        return 1
    print("VALID: {}".format(sys.argv[1]))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
