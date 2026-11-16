#!/usr/bin/env python3
"""Verify a pinned Graphify source checkout without installing or executing Graphify."""
from __future__ import annotations

import argparse
import ast
import subprocess
import sys
import tomllib
from pathlib import Path


class VerificationError(RuntimeError):
    pass


def git(root: Path, *args: str) -> str:
    try:
        return subprocess.check_output(
            ["git", "-C", str(root), *args],
            text=True,
            stderr=subprocess.STDOUT,
        ).strip()
    except subprocess.CalledProcessError as exc:
        raise VerificationError(f"git {' '.join(args)} failed: {exc.output.strip()}") from exc


def read_assignment(path: Path, name: str) -> object:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except (OSError, SyntaxError, UnicodeError) as exc:
        raise VerificationError(f"cannot parse {path}: {exc}") from exc

    matches = []
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == name for target in node.targets
        ):
            matches.append(node.value)
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name) and node.target.id == name:
            matches.append(node.value)

    if len(matches) != 1 or matches[0] is None:
        raise VerificationError(f"{name} must have exactly one literal top-level assignment")
    try:
        return ast.literal_eval(matches[0])
    except (ValueError, TypeError) as exc:
        raise VerificationError(f"{name} must be a literal constant") from exc


def verify_source(root: Path, *, expected_version: str, expected_commit: str,
                  expected_lock_blob: str, expected_schema: int, expected_tag: str) -> dict[str, object]:
    root = root.resolve()
    try:
        git_root = Path(git(root, "rev-parse", "--show-toplevel")).resolve()
    except VerificationError as exc:
        raise VerificationError("source root is not a Git checkout") from exc
    if git_root != root:
        raise VerificationError(f"source root must be the Git checkout root: expected {git_root}, got {root}")
    dirty = git(root, "status", "--porcelain", "--untracked-files=all")
    if dirty:
        raise VerificationError(f"source checkout is not clean: {dirty.splitlines()[0]}")
    actual_commit = git(root, "rev-parse", "HEAD")
    if actual_commit != expected_commit:
        raise VerificationError(f"source commit mismatch: expected {expected_commit}, got {actual_commit}")
    tag_commit = git(root, "rev-parse", f"refs/tags/{expected_tag}^{{}}")
    if tag_commit != expected_commit:
        raise VerificationError(f"tag target mismatch: expected {expected_commit}, got {tag_commit}")
    actual_lock_blob = git(root, "rev-parse", f"{expected_tag}:uv.lock")
    if actual_lock_blob != expected_lock_blob:
        raise VerificationError(f"uv.lock blob mismatch: expected {expected_lock_blob}, got {actual_lock_blob}")
    try:
        project = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError) as exc:
        raise VerificationError(f"cannot parse pyproject.toml: {exc}") from exc
    actual_version = project.get("project", {}).get("version")
    if actual_version != expected_version:
        raise VerificationError(f"package version mismatch: expected {expected_version}, got {actual_version!r}")
    actual_schema = read_assignment(root / "graphify" / "cache.py", "_AST_CACHE_SCHEMA")
    if type(actual_schema) is not int or actual_schema != expected_schema:
        raise VerificationError(f"AST cache schema mismatch: expected integer {expected_schema}, got {actual_schema!r}")
    return {"status": "PASS", "tag": expected_tag, "version": actual_version,
            "commit": actual_commit, "uv_lock_blob": actual_lock_blob,
            "ast_cache_schema": actual_schema, "graphify_install_performed": False,
            "graphify_extraction_performed": False}


def main() -> int:
    import json
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--version", required=True)
    parser.add_argument("--commit", required=True)
    parser.add_argument("--uv-lock-blob", required=True)
    parser.add_argument("--ast-cache-schema", type=int, required=True)
    parser.add_argument("--tag", required=True)
    args = parser.parse_args()
    try:
        print(json.dumps(verify_source(args.source_root, expected_version=args.version,
            expected_commit=args.commit, expected_lock_blob=args.uv_lock_blob,
            expected_schema=args.ast_cache_schema, expected_tag=args.tag), indent=2, sort_keys=True))
    except VerificationError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
