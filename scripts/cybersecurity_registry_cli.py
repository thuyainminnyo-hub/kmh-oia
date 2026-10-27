#!/usr/bin/env python3
"""Command-line interface for the KMH OIA cybersecurity registry pilot."""
import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

# Support direct execution as `python scripts/cybersecurity_registry_cli.py`.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.cybersecurity_registry import (
    RegistryError,
    authorize_execution,
    read_entries,
    save_version,
    verify_registry,
)


def load_json(path):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RegistryError(f"cannot read JSON input: {exc}") from exc


def build_parser():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)

    append = commands.add_parser("append", help="validate and append a versioned record")
    append.add_argument("--record", required=True, help="path to a JSON record")
    append.add_argument("--registry", required=True, help="path to the local JSONL registry")

    verify = commands.add_parser("verify", help="verify the registry hash chain")
    verify.add_argument("--registry", required=True, help="path to the local JSONL registry")

    latest = commands.add_parser("latest", help="print the latest version for a case ID")
    latest.add_argument("--registry", required=True, help="path to the local JSONL registry")
    latest.add_argument("--case-id", required=True)

    authorize = commands.add_parser("authorize", help="evaluate execution authorization; does not execute changes")
    authorize.add_argument("--record", required=True, help="path to a JSON record")
    authorize.add_argument("--action", required=True, help="requested action, e.g. remediate")
    authorize.add_argument("--now", help="optional ISO-8601 time with timezone for deterministic checks")

    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    try:
        if args.command == "append":
            entry = save_version(args.registry, load_json(args.record))
            print(json.dumps({"status": "APPENDED", "case_id": entry["case_id"], "version": entry["version"], "entry_hash": entry["entry_hash"]}, sort_keys=True))
            return 0
        if args.command == "verify":
            count = verify_registry(args.registry)
            print(json.dumps({"status": "PASS", "verified_entries": count}, sort_keys=True))
            return 0
        if args.command == "latest":
            matches = [e for e in read_entries(args.registry) if e["case_id"] == args.case_id]
            if not matches:
                print(f"NOT FOUND: {args.case_id}", file=sys.stderr)
                return 1
            print(json.dumps(matches[-1], indent=2, sort_keys=True))
            return 0
        if args.command == "authorize":
            now = datetime.fromisoformat(args.now.replace("Z", "+00:00")) if args.now else None
            allowed, reason = authorize_execution(load_json(args.record), args.action, now=now)
            print(json.dumps({"allowed": allowed, "reason": reason}, sort_keys=True))
            return 0 if allowed else 1
    except (RegistryError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
