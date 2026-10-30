#!/usr/bin/env python3
"""Inventory and assess GitHub Actions step, composite, and container dependencies."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

import yaml
from yaml.nodes import MappingNode, ScalarNode, SequenceNode
from yaml.constructor import ConstructorError

FULL_SHA = re.compile(r"^[0-9a-fA-F]{40}$")
LOCKED_COMMIT = re.compile(r"^sha1-[0-9a-fA-F]{40}$")
REMOTE_ACTION = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+(?:/[A-Za-z0-9_.-]+)*@([^@\s]+)$")
DIGEST = re.compile(r"@sha256:[0-9a-fA-F]{64}$")
LOCAL_PREFIXES = ("./", "$/")


class StrictLoader(yaml.SafeLoader):
    """Safe YAML loader rejecting duplicate keys."""


def _mapping(loader: StrictLoader, node: MappingNode, deep: bool = False) -> dict:
    loader.flatten_mapping(node)
    result = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        try:
            duplicate = key in result
        except TypeError as exc:
            raise ConstructorError("while constructing a mapping", node.start_mark,
                                   "unhashable mapping key", key_node.start_mark) from exc
        if duplicate:
            raise ConstructorError("while constructing a mapping", node.start_mark,
                                   f"duplicate mapping key {key!r}", key_node.start_mark)
        result[key] = loader.construct_object(value_node, deep=deep)
    return result


def _unknown_tag(loader: StrictLoader, node: Any) -> Any:
    if isinstance(node, ScalarNode):
        return loader.construct_scalar(node)
    if isinstance(node, SequenceNode):
        return loader.construct_sequence(node, deep=True)
    if isinstance(node, MappingNode):
        return loader.construct_mapping(node, deep=True)
    raise ConstructorError(None, None, "unsupported YAML node", node.start_mark)


StrictLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _mapping)
StrictLoader.add_constructor(None, _unknown_tag)


def load_yaml(path: Path) -> Any:
    with path.open(encoding="utf-8") as stream:
        return yaml.load(stream, Loader=StrictLoader)


def _local_action(root: Path, reference: str) -> tuple[Path | None, str | None]:
    prefix = next((item for item in LOCAL_PREFIXES if reference.startswith(item)), None)
    if prefix is None:
        return None, None
    relative = reference[len(prefix):]
    if not relative or "${{" in relative or "}}" in relative:
        return None, "local action path is empty or expression-based"
    candidate = (root / relative).resolve()
    try:
        candidate.relative_to(root.resolve())
    except ValueError:
        return None, "local action path escapes repository root"
    if candidate.is_file():
        return None, f"local action reference must identify a directory containing action.yml: {reference}"
    manifest = next((p for p in (candidate / "action.yml", candidate / "action.yaml") if p.is_file()), None)
    if manifest is None:
        return None, f"local action manifest action.yml/action.yaml not found: {reference}"
    return manifest, None


def audit(root: Path) -> dict[str, Any]:
    root = root.resolve()
    workflows_dir = root / ".github" / "workflows"
    errors: list[str] = []
    findings: list[dict[str, str]] = []
    references: list[dict[str, str]] = []
    scanned_workflows = 0
    scanned_composites = 0
    action_calls = 0
    container_refs = 0
    visited_composites: set[Path] = set()

    lockfile_path = root / ".github" / "workflows" / "actions.lock"
    lock_data = None
    if lockfile_path.is_file():
        try:
            lock_data = load_yaml(lockfile_path)
            if (not isinstance(lock_data, dict)
                    or not isinstance(lock_data.get("workflows"), dict)
                    or not isinstance(lock_data.get("dependencies"), dict)
                    or not isinstance(lock_data.get("version"), str)):
                errors.append(".github/workflows/actions.lock: invalid lockfile structure")
                lock_data = None
        except (OSError, UnicodeError, yaml.YAMLError) as exc:
            errors.append(f".github/workflows/actions.lock: YAML parse error: {exc}")

    def valid_lock_entry(workflow_path: str, reference: str) -> tuple[bool, str | None]:
        if lock_data is None:
            return False, None
        workflow_entries = lock_data["workflows"].get(workflow_path)
        if not isinstance(workflow_entries, list) or reference not in workflow_entries:
            return False, None
        dependency = lock_data["dependencies"].get(reference)
        if not isinstance(dependency, dict):
            return False, None
        commit = dependency.get("commit")
        owner_id = dependency.get("owner_id")
        repo_id = dependency.get("repo_id")
        if (not isinstance(commit, str) or not LOCKED_COMMIT.fullmatch(commit)
                or not isinstance(owner_id, int) or owner_id <= 0
                or not isinstance(repo_id, int) or repo_id <= 0):
            return False, None
        return True, commit

    def record_issue(level: str, location: str, message: str) -> None:
        findings.append({"level": level, "location": location, "message": message})

    def check_container(image: Any, location: str) -> None:
        nonlocal container_refs
        container_refs += 1
        if not isinstance(image, str) or not image.strip():
            record_issue("HOLD", location, "container image must be a non-empty literal string")
        elif "${{" in image or "}}" in image:
            record_issue("HOLD", location, "dynamic container image cannot be digest-verified statically")
        elif not DIGEST.search(image.strip()):
            record_issue("HOLD", location, "container image must be pinned to an immutable sha256 digest")
        else:
            references.append({"location": location, "kind": "container", "reference": image.strip()})

    def scan_uses(reference: Any, location: str, workflow_path: str, depth: int = 0) -> None:
        nonlocal action_calls, scanned_composites
        action_calls += 1
        if not isinstance(reference, str) or not reference.strip():
            record_issue("HOLD", location, "step uses must be a non-empty string")
            return
        reference = reference.strip()
        if any(token in reference for token in ("\n", "\r", "${{", "}}")):
            record_issue("HOLD", location, "dynamic or multiline action reference cannot be verified")
            return
        if reference.startswith("docker://"):
            image = reference[len("docker://"):]
            check_container(image, location)
            return
        if reference.startswith(LOCAL_PREFIXES):
            manifest, error = _local_action(root, reference)
            if error:
                record_issue("HOLD", location, error)
                return
            references.append({"location": location, "kind": "local-composite", "reference": reference,
                               "manifest": manifest.relative_to(root).as_posix()})
            if manifest in visited_composites:
                return
            if depth >= 10:
                record_issue("HOLD", location, "local composite nesting exceeds the supported audit depth of 10")
                return
            visited_composites.add(manifest)
            scanned_composites += 1
            try:
                document = load_yaml(manifest)
            except (OSError, UnicodeError, yaml.YAMLError) as exc:
                errors.append(f"{manifest.relative_to(root).as_posix()}: YAML parse error: {exc}")
                return
            runs = document.get("runs") if isinstance(document, dict) else None
            steps = runs.get("steps") if isinstance(runs, dict) and runs.get("using") == "composite" else None
            if not isinstance(steps, list):
                record_issue("HOLD", manifest.relative_to(root).as_posix(),
                             "local action is not a structurally valid composite action")
                return
            scan_steps(steps, manifest.relative_to(root).as_posix(), workflow_path, depth + 1)
            return

        match = REMOTE_ACTION.fullmatch(reference)
        if not match:
            record_issue("HOLD", location, f"unrecognized action reference syntax: {reference}")
            return
        ref = match.group(1)
        if lock_data is not None:
            locked, commit = valid_lock_entry(workflow_path, reference)
            if not locked:
                record_issue("HOLD", location,
                             f"remote action is not covered by a valid actions.lock entry for {workflow_path}: {reference}")
                return
            references.append({"location": location, "kind": "locked-remote-action",
                               "reference": reference, "locked_commit": commit})
            return
        if not FULL_SHA.fullmatch(ref):
            record_issue("HOLD", location, f"remote action is not pinned to a full 40-character commit SHA: {reference}")
            return
        references.append({"location": location, "kind": "remote-action", "reference": reference})

    def scan_steps(steps: Any, owner: str, workflow_path: str, depth: int = 0) -> None:
        if not isinstance(steps, list):
            record_issue("HOLD", owner, "steps must be a YAML sequence")
            return
        for index, step in enumerate(steps):
            location = f"{owner} step[{index}]"
            if not isinstance(step, dict):
                record_issue("HOLD", location, "step must be a YAML mapping")
                continue
            if "uses" in step:
                scan_uses(step["uses"], location, workflow_path, depth)

    if not workflows_dir.is_dir():
        errors.append("workflow directory not found")
        files: list[Path] = []
    else:
        files = sorted(p for p in workflows_dir.rglob("*") if p.is_file() and p.suffix.lower() in {".yml", ".yaml"})
        if not files:
            errors.append("no workflow YAML files found")

    for path in files:
        scanned_workflows += 1
        relative = path.relative_to(root).as_posix()
        try:
            document = load_yaml(path)
        except (OSError, UnicodeError, yaml.YAMLError) as exc:
            errors.append(f"{relative}: YAML parse error: {exc}")
            continue
        if not isinstance(document, dict):
            errors.append(f"{relative}: workflow root must be a YAML mapping")
            continue
        jobs = document.get("jobs")
        if not isinstance(jobs, dict):
            errors.append(f"{relative}: jobs must be a YAML mapping")
            continue
        for job_id, job in jobs.items():
            location = f"{relative} job {job_id!r}"
            if not isinstance(job, dict):
                record_issue("HOLD", location, "job must be a YAML mapping")
                continue
            if "uses" in job:
                record_issue("HOLD", location, "reusable workflow call requires separate workflow-reference audit")
            if "container" in job:
                container = job["container"]
                check_container(container.get("image") if isinstance(container, dict) else container,
                                location + " container")
            services = job.get("services", {})
            if services is not None and not isinstance(services, dict):
                record_issue("HOLD", location + " services", "services must be a YAML mapping")
            elif isinstance(services, dict):
                for service_name, service in services.items():
                    if isinstance(service, dict):
                        check_container(service.get("image"), location + f" service {service_name!r}")
                    else:
                        record_issue("HOLD", location + f" service {service_name!r}",
                                     "service definition must be a YAML mapping")
            if "steps" in job:
                scan_steps(job["steps"], location, relative)

    status = "HOLD" if errors or findings else "PASS"
    return {
        "schema_version": "1.0",
        "status": status,
        "decision": "HOLD" if status == "HOLD" else "REVIEW_READY",
        "workflow_files_scanned": scanned_workflows,
        "composite_action_manifests_scanned": scanned_composites,
        "action_uses_checked": action_calls,
        "container_references_checked": container_refs,
        "lockfile_present": lock_data is not None,
        "lockfile_workflows": len(lock_data["workflows"]) if lock_data is not None else 0,
        "lockfile_dependencies": len(lock_data["dependencies"]) if lock_data is not None else 0,
        "verified_references": references,
        "findings": findings,
        "errors": errors,
        "scope": [
            "Workflow step-level remote action references and local composite actions",
            "Nested uses references inside local composite action manifests",
            "docker:// step images and job/service container image digests",
            "Reusable workflow job calls remain covered by audit_reusable_workflow_refs.py",
            "When actions.lock exists, remote action references require an exact workflow entry and structurally valid repository identity plus locked commit; gh actions-lock --verify independently checks upstream provenance",
            "Without actions.lock, remote action references require full 40-character commit SHAs",
            "This audit does not prove action source safety or complete runtime dependency coverage",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = audit(args.root)
    rendered = json.dumps(result, indent=2, sort_keys=True)
    print(rendered)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
    # Findings are a governance HOLD, not an audit execution crash. Malformed
    # YAML and filesystem errors are still represented separately in the report.
    return 1 if result["errors"] else 0


if __name__ == "__main__":
    sys.exit(main())
