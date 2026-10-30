#!/usr/bin/env python3
"""Fail-closed structural audit of GitHub Actions reusable workflow references."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

import yaml
from yaml.constructor import ConstructorError
from yaml.nodes import MappingNode, ScalarNode, SequenceNode

REMOTE_WORKFLOW = re.compile(
    r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+/\.github/workflows/"
    r"(?:[A-Za-z0-9_.-]+/)*[A-Za-z0-9_.-]+\.ya?ml@([^@\s]+)$"
)
FULL_COMMIT_SHA = re.compile(r"^[0-9a-fA-F]{40}$")
LOCAL_PREFIXES = ("./.github/workflows/", "$/.github/workflows/")


class StrictWorkflowLoader(yaml.SafeLoader):
    """Safe YAML loader that rejects duplicate mapping keys."""


def _construct_strict_mapping(loader: StrictWorkflowLoader, node: MappingNode, deep: bool = False) -> dict:
    loader.flatten_mapping(node)
    result = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        try:
            duplicate = key in result
        except TypeError as exc:
            raise ConstructorError(
                "while constructing a mapping", node.start_mark,
                "found an unhashable mapping key", key_node.start_mark,
            ) from exc
        if duplicate:
            raise ConstructorError(
                "while constructing a mapping", node.start_mark,
                f"duplicate mapping key {key!r}", key_node.start_mark,
            )
        result[key] = loader.construct_object(value_node, deep=deep)
    return result


def _construct_unknown_tag(loader: StrictWorkflowLoader, node: Any) -> Any:
    """Treat GitHub-specific YAML tags as opaque data, never execute them."""
    if isinstance(node, ScalarNode):
        return loader.construct_scalar(node)
    if isinstance(node, SequenceNode):
        return loader.construct_sequence(node, deep=True)
    if isinstance(node, MappingNode):
        return loader.construct_mapping(node, deep=True)
    raise ConstructorError(None, None, "unsupported YAML node type", node.start_mark)


StrictWorkflowLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _construct_strict_mapping
)
StrictWorkflowLoader.add_constructor(None, _construct_unknown_tag)


def _local_target(root: Path, reference: str) -> tuple[Path | None, str | None]:
    prefix = next((item for item in LOCAL_PREFIXES if reference.startswith(item)), None)
    if prefix is None:
        return None, None
    relative = reference[len(prefix):]
    if not relative or Path(relative).suffix.lower() not in {".yml", ".yaml"}:
        return None, "local reusable workflow path must identify a .yml or .yaml file"
    target = (root / ".github" / "workflows" / relative).resolve()
    workflows_root = (root / ".github" / "workflows").resolve()
    try:
        target.relative_to(workflows_root)
    except ValueError:
        return None, "local reusable workflow path escapes .github/workflows"
    if not target.is_file():
        return None, f"local reusable workflow target does not exist: {reference}"
    return target, None


def _load_workflow(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as stream:
        return yaml.load(stream, Loader=StrictWorkflowLoader)


def audit(root: Path) -> tuple[list[str], int, int, list[dict[str, str]]]:
    root = root.resolve()
    workflows_root = root / ".github" / "workflows"
    if not workflows_root.is_dir():
        return [f"workflow directory not found: {workflows_root}"], 0, 0, []

    files = sorted(
        path for path in workflows_root.rglob("*")
        if path.is_file() and path.suffix.lower() in {".yml", ".yaml"}
    )
    if not files:
        return ["no workflow YAML files found"], 0, 0, []

    errors: list[str] = []
    references: list[dict[str, str]] = []
    checked = 0

    for path in files:
        relative_path = path.relative_to(root).as_posix()
        try:
            document = _load_workflow(path)
        except (OSError, UnicodeError, yaml.YAMLError) as exc:
            errors.append(f"{relative_path}: YAML parse/structure error: {exc}")
            continue

        if not isinstance(document, dict):
            errors.append(f"{relative_path}: workflow root must be a YAML mapping")
            continue

        jobs = document.get("jobs")
        if not isinstance(jobs, dict):
            errors.append(f"{relative_path}: 'jobs' must be a YAML mapping")
            continue

        for job_id, job in jobs.items():
            if not isinstance(job, dict):
                errors.append(f"{relative_path}: job {job_id!r} must be a YAML mapping")
                continue
            if "uses" not in job:
                continue

            checked += 1
            reference = job["uses"]
            label = f"{relative_path} job {job_id!r}"
            if not isinstance(reference, str) or not reference.strip():
                errors.append(f"{label}: reusable workflow 'uses' must be a non-empty string")
                continue
            reference = reference.strip()

            if any(token in reference for token in ("\n", "\r", "${{", "}}")):
                errors.append(f"{label}: multiline or expression-based workflow references are not allowed")
                continue

            if reference.startswith(LOCAL_PREFIXES):
                target, error = _local_target(root, reference)
                if error:
                    errors.append(f"{label}: {error}")
                else:
                    references.append({
                        "workflow": relative_path,
                        "job": str(job_id),
                        "reference": reference,
                        "kind": "local",
                        "resolved_path": target.relative_to(root).as_posix(),
                    })
                continue

            match = REMOTE_WORKFLOW.fullmatch(reference)
            if not match:
                errors.append(f"{label}: malformed remote reusable workflow reference: {reference}")
                continue
            ref = match.group(1)
            if not FULL_COMMIT_SHA.fullmatch(ref):
                errors.append(
                    f"{label}: remote reusable workflow must use a full 40-character commit SHA: {reference}"
                )
                continue

            references.append({
                "workflow": relative_path,
                "job": str(job_id),
                "reference": reference,
                "kind": "remote",
            })

    return errors, len(files), checked, references


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output", type=Path, help="write the JSON evidence report to this path")
    args = parser.parse_args()

    errors, scanned, checked, references = audit(args.root)
    result = {
        "schema_version": "1.0",
        "status": "HOLD" if errors else "PASS",
        "workflow_files_scanned": scanned,
        "reusable_workflow_calls_checked": checked,
        "references": references,
        "errors": errors,
    }
    rendered = json.dumps(result, indent=2, sort_keys=True)
    print(rendered)

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")

    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
