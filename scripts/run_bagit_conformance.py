"""Run the Library of Congress BagIt fixture corpus and retain per-fixture JSON evidence."""
from __future__ import annotations

import argparse
import json
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--suite-path", required=True, type=Path)
    parser.add_argument("--suite-commit", required=True)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    suite = args.suite_path.resolve()
    version_dir = suite / "v1.0"
    if not version_dir.is_dir():
        raise SystemExit(f"Missing BagIt v1.0 fixture directory: {version_dir}")
    system = platform.system().lower()
    categories = ["valid", "invalid", "warning", "linux-only", "windows-only"]
    records = []
    failures = []

    for category in categories:
        if category == "linux-only" and system != "linux":
            continue
        if category == "windows-only" and system != "windows":
            continue
        folder = version_dir / category
        if not folder.is_dir():
            continue
        for bag_path in sorted(p for p in folder.iterdir() if p.is_dir()):
            proc = subprocess.run(
                [sys.executable, "-m", "bagit", "--validate", str(bag_path)],
                capture_output=True,
                text=True,
                check=False,
            )
            if category == "valid":
                passed = proc.returncode == 0
            elif category in ("invalid", "linux-only", "windows-only"):
                passed = proc.returncode != 0
            else:  # Warning fixtures are valid bags; warnings are retained verbatim.
                passed = proc.returncode == 0
            record = {
                "fixture": bag_path.name,
                "category": category,
                "expected": "valid" if category in ("valid", "warning") else "invalid",
                "exit_code": proc.returncode,
                "passed": passed,
                "stdout": proc.stdout,
                "stderr": proc.stderr,
                "warning_observed": bool(proc.stderr.strip()) if category == "warning" else False,
            }
            records.append(record)
            if not passed:
                failures.append(record)

    if not records:
        raise SystemExit("No BagIt v1.0 conformance fixtures were discovered")

    result = {
        "schema": "kmh.bagit-conformance-report.v1",
        "suite": "LibraryOfCongress/bagit-conformance-suite",
        "suite_version": "v1.0",
        "suite_commit": args.suite_commit,
        "validator": "LibraryOfCongress/bagit-python",
        "validator_version": __import__("importlib.metadata", fromlist=["version"]).version("bagit"),
        "platform": platform.platform(),
        "python_version": platform.python_version(),
        "run_at_utc": datetime.now(timezone.utc).isoformat(),
        "fixture_count": len(records),
        "passed_count": sum(1 for r in records if r["passed"]),
        "failed_count": len(failures),
        "records": records,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({k: result[k] for k in ("fixture_count", "passed_count", "failed_count")}, indent=2))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
