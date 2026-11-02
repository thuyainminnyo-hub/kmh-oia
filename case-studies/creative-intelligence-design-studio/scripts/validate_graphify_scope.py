#!/usr/bin/env python3
"""Fail-closed preflight validator for the isolated Graphify sandbox.

This script never installs Graphify, starts indexing, invokes a model, or runs a shell command.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = PROJECT_ROOT / "contracts" / "graphify-scope-policy.json"
EXPECTED_SCAN_ROOT = "graphify-sandbox"
EXPECTED_ALLOWED_PATHS = [".graphifyignore", "src/"]
EXPECTED_EXTENSIONS = [".py"]
REQUIRED_DENY_PATTERNS = {
    ".env",
    ".env.*",
    ".envrc",
    "**/.env",
    "**/.env.*",
    "**/.envrc",
    "**/*.pem",
    "**/*.key",
    "**/*.p12",
    "**/*.pfx",
    "**/*.crt",
    "**/*secret*",
    "**/*credential*",
    "**/.netrc",
    "**/.npmrc",
    "**/.pypirc",
    "**/.git-credentials",
    "**/id_rsa",
    "**/id_ed25519",
    "**/.ssh/**",
    "**/private/**",
    "**/learner-data/**",
    "**/raw-assets/**",
    "**/generated-media/**",
    "**/media/**",
    "**/graphify-out/**",
}
REQUIRED_FIXTURES = {
    ".graphifyignore",
    "src/contract_guard.py",
    "src/outfit_flow.py",
}
SENSITIVE_EXACT_NAMES = {
    ".env",
    ".envrc",
    ".netrc",
    ".npmrc",
    ".pypirc",
    ".git-credentials",
    "id_rsa",
    "id_ed25519",
}
SENSITIVE_SUFFIXES = {".pem", ".key", ".p12", ".pfx", ".crt"}
SENSITIVE_DIRECTORY_NAMES = {
    ".ssh",
    "private",
    "learner-data",
    "raw-assets",
    "generated-media",
    "media",
    "graphify-out",
}


def _is_sensitive_path(relative_path: str) -> bool:
    parts = [part.lower() for part in Path(relative_path).parts]
    for part in parts:
        if part in SENSITIVE_EXACT_NAMES or part in SENSITIVE_DIRECTORY_NAMES:
            return True
        if part.startswith(".env.") or "secret" in part or "credential" in part:
            return True
        if Path(part).suffix in SENSITIVE_SUFFIXES:
            return True
    return False


def validate_graphify_scope(policy: dict[str, Any], project_root: Path) -> list[str]:
    """Return policy or filesystem violations; an empty list means preflight PASS."""
    errors: list[str] = []

    if policy.get("policy_version") != "1.0.0":
        errors.append("policy_version must be 1.0.0")
    if policy.get("status") != "preflight_only":
        errors.append("status must remain preflight_only until a separate approval")

    provider = policy.get("provider")
    if not isinstance(provider, dict):
        errors.append("provider must be an object")
    else:
        if provider.get("name") != "Graphify":
            errors.append("provider name must be Graphify")
        if provider.get("source_repository") != "https://github.com/Graphify-Labs/graphify":
            errors.append("provider source must be the official Graphify-Labs repository")
        if provider.get("package_name") != "graphifyy":
            errors.append("package_name must be the official graphifyy package")
        if provider.get("approved_version") is not None:
            errors.append("approved_version must remain unset before owner review")
        if provider.get("version_pin_required") is not True:
            errors.append("version_pin_required must be true")

    scope = policy.get("scope")
    if not isinstance(scope, dict):
        errors.append("scope must be an object")
        scope = {}
    if scope.get("scan_root") != EXPECTED_SCAN_ROOT:
        errors.append("scan_root must be the isolated graphify-sandbox directory")
    if scope.get("allowed_paths") != EXPECTED_ALLOWED_PATHS:
        errors.append("allowed_paths must remain exactly .graphifyignore and src/")
    if scope.get("allowed_extensions") != EXPECTED_EXTENSIONS:
        errors.append("allowed_extensions must remain exactly .py")
    max_files = scope.get("max_files")
    if type(max_files) is not int or not 1 <= max_files <= 20:
        errors.append("max_files must be an integer between 1 and 20")
    if scope.get("allow_symlinks") is not False:
        errors.append("allow_symlinks must be false")

    execution = policy.get("execution")
    if not isinstance(execution, dict):
        errors.append("execution must be an object")
        execution = {}
    for flag in (
        "install_allowed",
        "index_allowed",
        "assistant_skill_install_allowed",
        "git_hook_install_allowed",
        "global_graph_merge_allowed",
    ):
        if execution.get(flag) is not False:
            errors.append(f"{flag} must remain false during preflight")
    if execution.get("semantic_backend") != "none":
        errors.append("semantic_backend must be none")
    if execution.get("code_only_required") is not True:
        errors.append("code_only_required must be true")

    deny_patterns = policy.get("deny_patterns")
    if not isinstance(deny_patterns, list):
        errors.append("deny_patterns must be a list")
    else:
        missing = sorted(REQUIRED_DENY_PATTERNS - set(deny_patterns))
        if missing:
            errors.append("missing required deny patterns: " + ", ".join(missing))
        if any(not isinstance(item, str) or item.startswith("!") for item in deny_patterns):
            errors.append("deny_patterns must be strings and must not re-include excluded paths")

    gates = policy.get("review_gates")
    if not isinstance(gates, list) or not gates:
        errors.append("review_gates must be a non-empty list")

    project_root = Path(project_root).resolve()
    sandbox_root = project_root / EXPECTED_SCAN_ROOT
    if sandbox_root.is_symlink():
        errors.append("scan root must not be a symlink")
        return errors
    if not sandbox_root.exists() or not sandbox_root.is_dir():
        errors.append("isolated graphify-sandbox directory is missing")
        return errors
    try:
        sandbox_root.resolve(strict=True).relative_to(project_root)
    except (OSError, ValueError):
        errors.append("scan root must resolve inside the Creative Studio project")
        return errors

    ignore_file = sandbox_root / ".graphifyignore"
    if not ignore_file.is_file() or ignore_file.is_symlink():
        errors.append("sandbox .graphifyignore is missing or is not a regular file")
    else:
        ignore_lines = set(ignore_file.read_text(encoding="utf-8").splitlines())
        required_ignore_lines = {
            "**/.env",
            "**/.env.*",
            "**/*.pem",
            "**/*.key",
            "**/.ssh/**",
            "**/private/**",
            "**/learner-data/**",
            "**/raw-assets/**",
            "**/media/**",
            "**/graphify-out/**",
        }
        missing_ignore = sorted(required_ignore_lines - ignore_lines)
        if missing_ignore:
            errors.append("sandbox .graphifyignore is missing: " + ", ".join(missing_ignore))

    src_dir = sandbox_root / "src"
    if not src_dir.is_dir() or src_dir.is_symlink():
        errors.append("sandbox src/ directory is missing or is not a regular directory")

    observed_files: set[str] = set()
    file_count = 0
    for entry in sorted(sandbox_root.rglob("*")):
        relative = entry.relative_to(sandbox_root).as_posix()
        if entry.is_symlink():
            errors.append(f"symlink is not allowed in sandbox: {relative}")
            continue
        if _is_sensitive_path(relative):
            errors.append(f"sensitive path is not allowed in sandbox: {relative}")
            continue
        if entry.is_dir():
            if relative != "src" and not relative.startswith("src/"):
                errors.append(f"directory is outside the approved src/ path: {relative}")
            continue

        file_count += 1
        observed_files.add(relative)
        allowed = relative == ".graphifyignore" or (
            relative.startswith("src/") and Path(relative).suffix == ".py"
        )
        if not allowed:
            errors.append(f"file is outside the approved Python fixture allowlist: {relative}")

    if file_count > max_files if isinstance(max_files, int) else False:
        errors.append(f"sandbox contains {file_count} files; policy maximum is {max_files}")
    missing_fixtures = sorted(REQUIRED_FIXTURES - observed_files)
    if missing_fixtures:
        errors.append("required synthetic fixtures are missing: " + ", ".join(missing_fixtures))

    return errors


def main() -> int:
    try:
        policy = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"FAIL: cannot read Graphify scope policy: {exc}")
        return 2

    errors = validate_graphify_scope(policy, PROJECT_ROOT)
    if errors:
        print("FAIL: Graphify scope preflight")
        for error in errors:
            print(f"- {error}")
        return 1

    print("PASS: Graphify scope preflight — isolated synthetic Python fixture only")
    print("Graphify install/indexing/model execution: NOT RUN (approval required)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
