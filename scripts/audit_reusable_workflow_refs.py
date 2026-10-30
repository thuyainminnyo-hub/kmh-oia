#!/usr/bin/env python3
"""Audit job-level reusable workflow references in GitHub Actions YAML."""
import argparse
import json
import re
import sys
from pathlib import Path

REMOTE = re.compile(
    r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+/\.github/workflows/"
    r"(?:[A-Za-z0-9_.-]+/)*[A-Za-z0-9_.-]+\.ya?ml@([^@\s]+)$"
)
SHA = re.compile(r"^[0-9a-fA-F]{40}$")
JOB_HEADER = re.compile(r"^  ([^\s#][^:]*):\s*(?:#.*)?$")
JOB_USES = re.compile(r"^    uses:\s*(.*?)\s*$")
LOCAL_PREFIXES = ("./.github/workflows/", "$/.github/workflows/")


def audit(root):
    folder = root / ".github" / "workflows"
    if not folder.is_dir():
        return [f"workflow directory not found: {folder}"], 0, 0
    errors, scanned, checked = [], 0, 0
    for path in sorted(folder.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in (".yml", ".yaml"):
            continue
        scanned += 1
        in_jobs = False
        current_job = None
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except OSError as exc:
            errors.append(f"{path.relative_to(root)}: cannot read workflow: {exc}")
            continue
        for line_number, line in enumerate(lines, 1):
            if line == "jobs:":
                in_jobs = True
                current_job = None
                continue
            if not in_jobs:
                continue
            if line and not line.startswith(" "):
                in_jobs = False
                current_job = None
                continue
            job_match = JOB_HEADER.match(line)
            if job_match:
                current_job = job_match.group(1).strip().strip("'").strip('"')
                continue
            if current_job is None:
                continue
            uses_match = JOB_USES.match(line)
            if not uses_match:
                continue
            checked += 1
            ref = uses_match.group(1).strip()
            ref = ref.split(" #", 1)[0].strip().strip("'").strip('"')
            label = f"{path.relative_to(root)}:{line_number} job {current_job!r}"
            if not ref:
                errors.append(f"{label}: empty or multiline uses value is not supported")
                continue
            if ref.startswith(LOCAL_PREFIXES):
                prefix = next(p for p in LOCAL_PREFIXES if ref.startswith(p))
                relative = ref[len(prefix):]
                target = (folder / relative).resolve()
                try:
                    target.relative_to(folder.resolve())
                except ValueError:
                    errors.append(f"{label}: local workflow path escapes workflow directory")
                    continue
                if not target.is_file():
                    errors.append(f"{label}: local workflow target does not exist: {ref}")
                continue
            match = REMOTE.fullmatch(ref)
            if not match:
                errors.append(f"{label}: malformed remote reusable workflow reference: {ref}")
            elif not SHA.fullmatch(match.group(1)):
                errors.append(f"{label}: remote reusable workflow must use a full 40-character SHA: {ref}")
    return errors, scanned, checked


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    errors, scanned, checked = audit(args.root.resolve())
    print(json.dumps({
        "status": "HOLD" if errors else "PASS",
        "workflow_files_scanned": scanned,
        "reusable_workflow_calls_checked": checked,
        "errors": errors,
    }, indent=2))
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
