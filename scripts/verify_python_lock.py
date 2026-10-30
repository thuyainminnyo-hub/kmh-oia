#!/usr/bin/env python3
"""Verify the reviewed, platform-specific, hash-locked CI dependency contract."""
from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import platform
import re
import sys
from pathlib import Path

EXPECTED = {
    "attrs": "25.4.0",
    "jsonschema": "4.26.0",
    "jsonschema-specifications": "2025.9.1",
    "pyyaml": "6.0.3",
    "referencing": "0.37.0",
    "rpds-py": "0.30.0",
    "typing-extensions": "4.15.0",
}
WORKFLOWS = (
    ".github/workflows/test.yml",
    ".github/workflows/validation.yml",
    ".github/workflows/prompt-library-schema-qa.yml",
    ".github/workflows/action-dependency-assurance.yml",
    ".github/workflows/reusable-workflow-sha-audit.yml",
)
REQ = re.compile(r"^([A-Za-z0-9_.-]+)==([A-Za-z0-9_.+!-]+)\s+--hash=sha256:([0-9a-f]{64})$")


def normalize(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


def parse_lock(path: Path) -> tuple[dict[str, tuple[str, str]], list[str]]:
    errors: list[str] = []
    if not path.is_file():
        return {}, [f"lockfile missing: {path}"]
    logical: list[str] = []
    pending = ""
    for number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.endswith("\\"):
            pending += line[:-1].strip() + " "
            continue
        logical.append(pending + line)
        pending = ""
    if pending:
        errors.append("lockfile ends with an incomplete continuation")
    parsed: dict[str, tuple[str, str]] = {}
    for item in logical:
        match = REQ.fullmatch(item)
        if not match:
            errors.append(f"invalid or unhashed lock entry: {item}")
            continue
        raw_name, version, digest = match.groups()
        name = normalize(raw_name)
        if name in parsed:
            errors.append(f"duplicate normalized package entry: {name}")
        parsed[name] = (version, digest)
    return parsed, errors


def audit(root: Path, verify_installed: bool = False, wheelhouse: Path | None = None) -> dict:
    root = root.resolve()
    lock_path = root / "requirements-ci.lock"
    parsed, errors = parse_lock(lock_path)
    if parsed != {k: (v, parsed.get(k, ("", ""))[1]) for k, v in EXPECTED.items()}:
        missing = sorted(set(EXPECTED) - set(parsed))
        extra = sorted(set(parsed) - set(EXPECTED))
        changed = sorted(k for k in set(parsed) & set(EXPECTED) if parsed[k][0] != EXPECTED[k])
        if missing: errors.append("missing lock packages: " + ", ".join(missing))
        if extra: errors.append("unexpected lock packages: " + ", ".join(extra))
        if changed: errors.append("unexpected package versions: " + ", ".join(changed))

    for path_text in WORKFLOWS:
        path = root / path_text
        if not path.is_file():
            errors.append(f"required CI workflow missing: {path_text}")
            continue
        content = path.read_text(encoding="utf-8")
        install_lines = [line.strip() for line in content.splitlines()
                         if "pip install" in line and "requirements" in line]
        if not install_lines:
            errors.append(f"no locked dependency install found in {path_text}")
        for line in install_lines:
            if "requirements-ci.lock" not in line:
                errors.append(f"unlocked requirements install in {path_text}: {line}")
            if "--require-hashes" not in line or "--only-binary=:all:" not in line:
                errors.append(f"hash/binary enforcement missing in {path_text}: {line}")

    direct = root / "requirements.txt"
    if direct.is_file():
        for number, raw in enumerate(direct.read_text(encoding="utf-8").splitlines(), 1):
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            match = re.fullmatch(r"([A-Za-z0-9_.-]+)==([A-Za-z0-9_.+!-]+)", line)
            if not match:
                errors.append(f"requirements.txt:{number}: direct inputs must be exact pins")
                continue
            name, version = normalize(match.group(1)), match.group(2)
            if name not in parsed or parsed[name][0] != version:
                errors.append(f"direct input is not represented at the same version in lock: {line}")

    installed = {}
    if verify_installed:
        all_installed = {}
        for dist in importlib.metadata.distributions():
            name = dist.metadata.get("Name")
            version = dist.version
            if name:
                all_installed[normalize(name)] = version
        installed = {name: version for name, version in all_installed.items() if name in EXPECTED}
        extras = sorted(set(all_installed) - set(EXPECTED) - {"pip", "setuptools"})
        if extras:
            errors.append("unexpected installed distributions: " + ", ".join(extras))
        if installed != EXPECTED:
            errors.append(f"installed dependency set differs from lock: {installed}")

    wheel_evidence = []
    if wheelhouse is not None:
        if not wheelhouse.is_dir():
            errors.append(f"wheelhouse directory missing: {wheelhouse}")
        else:
            for file in sorted(wheelhouse.iterdir()):
                if not file.is_file():
                    continue
                digest = hashlib.sha256(file.read_bytes()).hexdigest()
                if digest not in {value[1] for value in parsed.values()}:
                    errors.append(f"wheelhouse file hash is not present in lock: {file.name}")
                wheel_evidence.append({"file": file.name, "sha256": digest, "size_bytes": file.stat().st_size})
            if len(wheel_evidence) != len(EXPECTED):
                errors.append(f"expected {len(EXPECTED)} wheels, found {len(wheel_evidence)}")

    status = "HOLD" if errors else "PASS"
    lock_hash = hashlib.sha256(lock_path.read_bytes()).hexdigest() if lock_path.is_file() else None
    return {
        "schema_version": 1,
        "status": status,
        "lockfile": "requirements-ci.lock",
        "lockfile_sha256": lock_hash,
        "target": {"python": "3.12", "os": "ubuntu-latest", "architecture": "x86_64",
                   "runtime_python": platform.python_version(), "platform": platform.platform()},
        "expected_package_count": len(EXPECTED),
        "locked_packages": [{"name": name, "version": version, "sha256": digest}
                            for name, (version, digest) in sorted(parsed.items())],
        "installed_package_check": installed if verify_installed else None,
        "wheelhouse": wheel_evidence,
        "errors": errors,
        "limitations": [
            "This lock is intentionally scoped to CPython 3.12 on ubuntu-latest x86_64; it is not a cross-platform application runtime lock.",
            "The lock covers direct CI tooling and its resolved Python transitive dependencies, not GitHub Action bundled Node.js dependencies.",
            "A verified wheel hash proves artifact byte identity, not that the package is vulnerability-free or trustworthy.",
            "The repository's application runtime source currently has no statically detected third-party imports; this is a separate CI tooling environment.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--verify-installed", action="store_true")
    parser.add_argument("--wheelhouse", type=Path)
    parser.add_argument("--evidence-out", type=Path)
    args = parser.parse_args()
    result = audit(args.root, args.verify_installed, args.wheelhouse)
    rendered = json.dumps(result, indent=2) + "\n"
    if args.evidence_out:
        args.evidence_out.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 1 if result["status"] != "PASS" else 0


if __name__ == "__main__":
    raise SystemExit(main())
