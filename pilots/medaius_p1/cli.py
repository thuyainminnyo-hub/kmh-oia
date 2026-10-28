"""CLI for the local synthetic-only Medaius P1 pilot."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

from pilots.medaius_p1.service import (
    DuplicatePatientID,
    InvalidFixture,
    PatientNotFound,
    load_patients,
    make_audit_event,
    retrieve_history,
)


def run(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Local synthetic patient-history retrieval pilot")
    parser.add_argument("--fixture", required=True, help="Path to synthetic JSON fixture")
    parser.add_argument("--patient-id", required=True, help="Exact synthetic patient ID")
    parser.add_argument("--request-id", default="local-p1-request", help="Non-sensitive audit correlation ID")
    parser.add_argument("--audit-file", help="Optional path for PHI-minimized JSONL audit events")
    args = parser.parse_args(argv)
    if not re.fullmatch(r"[A-Za-z0-9._:-]{1,80}", args.request_id):
        parser.error("request-id must be 1-80 characters: letters, digits, dot, underscore, colon or hyphen only")
    outcome = "ERROR"
    result: dict[str, Any]
    exit_code = 1
    try:
        patients = load_patients(args.fixture)
        result = retrieve_history(patients, args.patient_id)
        outcome = "SUCCESS"
        exit_code = 0
    except PatientNotFound:
        result = {"status": "NOT_FOUND", "message": "No exact patient ID match."}
        outcome = "NOT_FOUND"
        exit_code = 2
    except DuplicatePatientID:
        result = {"status": "BLOCKED", "message": "Duplicate exact patient IDs; retrieval blocked."}
        outcome = "BLOCKED"
        exit_code = 3
    except (InvalidFixture, ValueError) as exc:
        result = {"status": "ERROR", "message": str(exc)}
        outcome = "ERROR"
        exit_code = 1

    # Fail closed: do not emit the retrieved record if requested audit persistence fails.
    if args.audit_file:
        try:
            event = make_audit_event(args.request_id, outcome)
            audit_path = Path(args.audit_file)
            audit_path.parent.mkdir(parents=True, exist_ok=True)
            with audit_path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(event, sort_keys=True) + "\\n")
        except OSError:
            print("ERROR: audit event could not be persisted; result withheld.", file=sys.stderr)
            return 4

    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return exit_code


if __name__ == "__main__":
    sys.exit(run())
