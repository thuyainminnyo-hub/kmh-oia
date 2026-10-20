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
    Path("docs/runbooks/production-evidence-runtime.md"),
    Path("src/production_evidence_runtime.py"),
    Path(".github/workflows/validation.yml"),
)


def validate_repository() -> list[str]:
    failures: list[str] = []
    for path in REQUIRED_PATHS:
        if not path.exists():
            failures.append(f"missing required path: {path}")
    if not failures and not compileall.compile_dir("src", quiet=1):
        failures.append("source compilation failed")
    if not failures:
        runtime_config = Path("src/production_evidence_runtime.py").read_text(encoding="utf-8")
        required_contracts = (
            'require_durable_replay_store=True',
            'health_check()',
            'allowed_source_providers',
            'startswith("file:")',
        )
        for contract in required_contracts:
            if contract not in runtime_config:
                failures.append(f"production evidence runtime missing safety contract: {contract}")
    return failures


if __name__ == "__main__":
    failures = validate_repository()
    if failures:
        for failure in failures:
            print(failure)
        raise SystemExit(1)
    print("deployment preflight: ok")
