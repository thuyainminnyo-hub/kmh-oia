"""Deterministic deployment preflight checks for the KMH OIA repository."""

from __future__ import annotations

import compileall
from pathlib import Path


REQUIRED_PATHS = (
    Path("src"),
    Path("tests"),
    Path("scripts"),
    Path("docs/stage12-production-readiness.md"),
    Path("docs/stage13-deployment-runbook.md"),
    Path(".github/workflows/validation.yml"),
)


def validate_repository() -> list[str]:
    failures: list[str] = []
    for path in REQUIRED_PATHS:
        if not path.exists():
            failures.append(f"missing required path: {path}")
    if not failures and not compileall.compile_dir("src", quiet=1):
        failures.append("source compilation failed")
    return failures


if __name__ == "__main__":
    failures = validate_repository()
    if failures:
        for failure in failures:
            print(failure)
        raise SystemExit(1)
    print("deployment preflight: ok")
