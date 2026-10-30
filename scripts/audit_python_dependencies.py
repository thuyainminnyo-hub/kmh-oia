#!/usr/bin/env python3
"""Audit third-party imports in the KMH OIA Python runtime source tree.

This is a static source-import inventory, not proof that dynamic imports,
plugins, native libraries, or external services are absent.
"""
from __future__ import annotations

import argparse
import ast
import json
import re
import sys
from pathlib import Path
from typing import Any

IMPORT_TO_DISTRIBUTION = {
    "yaml": "PyYAML",
    "jsonschema": "jsonschema",
}
REQUIREMENT = re.compile(r"^([A-Za-z0-9][A-Za-z0-9_.-]*)(?:\[[^]]+\])?==([A-Za-z0-9_.+!-]+)$")


def parse_runtime_requirements(path: Path) -> dict[str, str]:
    declared: dict[str, str] = {}
    if not path.is_file():
        raise FileNotFoundError(f"runtime dependency manifest not found: {path}")
    for line_number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        match = REQUIREMENT.fullmatch(line)
        if not match:
            raise ValueError(
                f"{path}:{line_number}: requirements must use exact name==version pins; got {line!r}"
            )
        name, version = match.groups()
        normalized = re.sub(r"[-_.]+", "-", name).lower()
        declared[normalized] = version
    return declared


def audit(root: Path) -> dict[str, Any]:
    root = root.resolve()
    source = root / "src"
    manifest = root / "requirements-runtime.txt"
    errors: list[str] = []
    findings: list[str] = []
    imported_stdlib: set[str] = set()
    imported_local: set[str] = set()
    imported_external: set[str] = set()
    scanned_files = 0

    if not source.is_dir():
        errors.append("runtime source directory src/ not found")
        files: list[Path] = []
    else:
        files = sorted(source.rglob("*.py"))

    for path in files:
        scanned_files += 1
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except (OSError, UnicodeError, SyntaxError) as exc:
            errors.append(f"{path.relative_to(root).as_posix()}: parse error: {exc}")
            continue
        for node in ast.walk(tree):
            modules: list[str] = []
            if isinstance(node, ast.Import):
                modules.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                modules.append(node.module)
            for module in modules:
                top = module.split(".", 1)[0]
                if top == "__future__":
                    continue
                if top == "src":
                    imported_local.add(top)
                elif top in sys.stdlib_module_names:
                    imported_stdlib.add(top)
                else:
                    imported_external.add(top)

    try:
        declared = parse_runtime_requirements(manifest)
    except (OSError, UnicodeError, ValueError) as exc:
        errors.append(str(exc))
        declared = {}

    imported_distributions = {
        re.sub(r"[-_.]+", "-", IMPORT_TO_DISTRIBUTION.get(module, module)).lower()
        for module in imported_external
    }
    undeclared = sorted(imported_distributions - set(declared))
    if undeclared:
        findings.append(
            "Third-party runtime imports are missing exact pins in requirements-runtime.txt: "
            + ", ".join(undeclared)
        )
    declared_unused = sorted(set(declared) - imported_distributions)

    status = "HOLD" if errors or findings else "PASS"
    return {
        "schema_version": 1,
        "status": status,
        "source_root": "src/",
        "source_files_scanned": scanned_files,
        "stdlib_import_roots": sorted(imported_stdlib),
        "local_import_roots": sorted(imported_local),
        "third_party_import_roots": sorted(imported_external),
        "declared_runtime_distributions": declared,
        "undeclared_runtime_distributions": undeclared,
        "declared_but_not_imported": declared_unused,
        "findings": findings,
        "errors": errors,
        "limitations": [
            "AST analysis does not detect importlib-based dynamic imports, entry-point plugins, native extensions loaded outside Python imports, subprocess-installed tools, or external services.",
            "This inventory covers src/ runtime modules only; scripts/, tests/, GitHub Actions, and runner software are separate dependency scopes.",
            "A PASS means all statically detected third-party imports in src/ have exact runtime pins; it is not a complete deployment-environment SBOM.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = audit(args.root)
    rendered = json.dumps(result, indent=2) + "\n"
    if args.output:
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 1 if result["status"] != "PASS" else 0


if __name__ == "__main__":
    raise SystemExit(main())
