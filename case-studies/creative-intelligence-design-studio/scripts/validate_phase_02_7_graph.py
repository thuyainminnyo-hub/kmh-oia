#!/usr/bin/env python3
"""Validate one-run Phase 02.7 Graphify output against a synthetic Python AST matrix.

The raw graph is read-only. A separate EXTRACTED-only candidate is written for
review; INFERRED and AMBIGUOUS relationships remain review-only.
"""
from __future__ import annotations

import argparse
import ast
import collections
import copy
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
from typing import Any

VALID_CONFIDENCES = {"EXTRACTED", "INFERRED", "AMBIGUOUS"}


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _json_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _normalize_source(value: Any, scan_root: Path) -> str | None:
    if not isinstance(value, str) or not value.strip():
        return None
    raw = value.strip().replace("\\", "/")
    path = Path(raw)
    if path.is_absolute():
        try:
            return path.resolve().relative_to(scan_root.resolve()).as_posix()
        except (OSError, ValueError):
            return None
    pure = PurePosixPath(raw)
    if pure.is_absolute() or ".." in pure.parts:
        return None
    return pure.as_posix().removeprefix("./")


def _module_name(relative: str) -> str:
    path = PurePosixPath(relative).relative_to("src")
    parts = list(path.parts)
    if parts[-1] == "__init__.py":
        parts.pop()
    else:
        parts[-1] = PurePosixPath(parts[-1]).stem
    return ".".join(parts)


def _resolve_from_module(importer_module: str, importer_file: str, node: ast.ImportFrom) -> str | None:
    if node.level == 0:
        return node.module
    is_package_init = PurePosixPath(importer_file).name == "__init__.py"
    package_parts = importer_module.split(".") if is_package_init else importer_module.split(".")[:-1]
    for _ in range(node.level - 1):
        if not package_parts:
            return None
        package_parts.pop()
    if node.module:
        package_parts.extend(node.module.split("."))
    return ".".join(package_parts)


def _load_corpus(scan_root: Path, expected_files: list[str]):
    scan_root = Path(scan_root).resolve()
    if scan_root.is_symlink() or not scan_root.is_dir():
        raise ValueError("scan root is missing or unsafe")
    actual_files = sorted(
        path.relative_to(scan_root).as_posix()
        for path in scan_root.rglob("*")
        if path.is_file() or path.is_symlink()
    )
    expected_all = sorted([".graphifyignore", *expected_files])
    if actual_files != expected_all:
        raise ValueError(
            "scan snapshot file set differs from the one-run approval: "
            f"expected={expected_all}, observed={actual_files}"
        )
    if any((scan_root / item).is_symlink() for item in actual_files):
        raise ValueError("symlinks are forbidden in the approved scan snapshot")

    source_data, trees, modules, module_to_file = {}, {}, {}, {}
    for relative in expected_files:
        if not relative.startswith("src/") or not relative.endswith(".py"):
            raise ValueError(f"approved source path is not a Python file under src/: {relative}")
        path = scan_root / relative
        if not path.is_file() or path.is_symlink():
            raise ValueError(f"approved source file missing/unsafe: {relative}")
        text = path.read_text(encoding="utf-8")
        tree = ast.parse(text, filename=relative)
        module = _module_name(relative)
        source_data[relative] = text
        trees[relative] = tree
        modules[relative] = module
        if module in module_to_file:
            raise ValueError(f"duplicate Python module path: {module}")
        module_to_file[module] = relative
    return scan_root, source_data, trees, modules, module_to_file


def _parents(tree: ast.AST):
    result = {}
    for parent in ast.walk(tree):
        for child in ast.iter_child_nodes(parent):
            result[child] = parent
    return result


def _nearest_scope(node: ast.AST, parents: dict):
    current = node
    while current in parents:
        current = parents[current]
        if isinstance(current, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            return current
    return None


def _within(node: ast.AST, root: ast.AST, parents: dict) -> bool:
    current = node
    while current in parents:
        current = parents[current]
        if current is root:
            return True
    return node is root


def _scope_label(scope: ast.AST) -> str:
    return scope.name + "()" if isinstance(scope, (ast.FunctionDef, ast.AsyncFunctionDef)) else scope.name


def _top_level_scopes(tree: ast.Module):
    return [
        node for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
    ]


def _declarations(trees: dict[str, ast.Module], modules: dict[str, str]):
    by_module_name = collections.defaultdict(list)
    by_file_name = collections.defaultdict(list)
    for relative, tree in trees.items():
        for node in tree.body:
            if isinstance(node, ast.ClassDef):
                record = {"name": node.name, "kind": "class", "line": node.lineno, "node": node, "file": relative}
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                record = {"name": node.name, "kind": "function", "line": node.lineno, "node": node, "file": relative}
            else:
                continue
            by_module_name[(modules[relative], node.name)].append(record)
            by_file_name[(relative, node.name)].append(record)
    return by_module_name, by_file_name


def _collect_imports(trees, modules, module_to_file, declarations):
    imports, errors = [], []
    for relative, tree in sorted(trees.items()):
        importer_module = modules[relative]
        for node in tree.body:
            if not isinstance(node, ast.ImportFrom):
                continue
            target_module = _resolve_from_module(importer_module, relative, node)
            if not target_module or target_module not in module_to_file:
                continue  # Explicitly outside the synthetic project corpus.
            target_file = module_to_file[target_module]
            for alias in node.names:
                if alias.name == "*":
                    errors.append({"code": "STAR_IMPORT_NOT_ALLOWED", "file": relative, "line": node.lineno})
                    continue
                found = declarations.get((target_module, alias.name), [])
                if len(found) != 1:
                    errors.append({
                        "code": "INTERNAL_IMPORT_NOT_UNIQUE",
                        "file": relative, "line": node.lineno,
                        "module": target_module, "name": alias.name, "count": len(found),
                    })
                    continue
                imported = found[0]
                imports.append({
                    "importer_file": relative,
                    "importer_module": importer_module,
                    "import_line": node.lineno,
                    "target_module": target_module,
                    "target_file": target_file,
                    "imported_name": alias.name,
                    "local_name": alias.asname or alias.name,
                    "target_kind": imported["kind"],
                    "target_line": imported["line"],
                })
    return imports, errors


def _annotation_roots(scope: ast.AST):
    roots = []
    if isinstance(scope, (ast.FunctionDef, ast.AsyncFunctionDef)):
        args = [*scope.args.posonlyargs, *scope.args.args, *scope.args.kwonlyargs]
        if scope.args.vararg:
            args.append(scope.args.vararg)
        if scope.args.kwarg:
            args.append(scope.args.kwarg)
        roots.extend((arg.annotation, "parameter_type") for arg in args if arg.annotation is not None)
        if scope.returns is not None:
            roots.append((scope.returns, "return_type"))
    for item in ast.walk(scope):
        if isinstance(item, ast.AnnAssign):
            roots.append((item.annotation, "variable_type"))
    return roots


def _references(scope: ast.AST, local_name: str, parents: dict):
    annotations = _annotation_roots(scope)
    bases = list(scope.bases) if isinstance(scope, ast.ClassDef) else []
    result = []
    for item in ast.walk(scope):
        if not isinstance(item, ast.Name) or item.id != local_name or not isinstance(item.ctx, ast.Load):
            continue
        if _nearest_scope(item, parents) is not scope:
            continue
        annotation_context = next((kind for root, kind in annotations if _within(item, root, parents)), None)
        if annotation_context:
            category, context = "TYPE_ANNOTATION", annotation_context
            relation = "references"
        elif any(_within(item, base, parents) for base in bases):
            category, context, relation = "CLASS_BASE", "base", "inherits"
        elif isinstance(parents.get(item), ast.Call) and parents[item].func is item:
            category, context, relation = "RUNTIME_CALL", "call", "calls"
        else:
            category, context, relation = "RUNTIME_BODY_REFERENCE", None, None
        result.append({
            "line": item.lineno, "category": category, "context": context,
            "relation": relation, "local_name": local_name,
        })
    return sorted(result, key=lambda x: (x["line"], x["category"], str(x["context"])))


def _node_label(name: str, kind: str) -> str:
    return f"{name}()" if kind == "function" else name


def _matching_nodes(nodes, source_file, label, line, scan_root):
    return [
        node for node in nodes
        if isinstance(node, dict)
        and node.get("file_type") == "code"
        and _normalize_source(node.get("source_file"), scan_root) == source_file
        and node.get("label") == label
        and node.get("source_location") == f"L{line}"
    ]


def _matching_edges(edges, source_id, target_id, relation, source_file, line, context):
    """Match graph evidence by identity, relation, and source provenance.

    A None context deliberately means the extractor does not emit a context
    discriminator for this relation (currently class inheritance).
    """
    return [
        edge for edge in edges
        if isinstance(edge, dict)
        and edge.get("source") == source_id
        and edge.get("target") == target_id
        and edge.get("relation") == relation
        and edge.get("confidence") == "EXTRACTED"
        and edge.get("source_file") == source_file
        and edge.get("source_location") == f"L{line}"
        and (context is None or edge.get("context") == context)
    ]


def _coalesced_parameter_return(scope: ast.AST, local_name: str, line: int) -> bool:
    """True only when the same imported name is both parameter and return type
    on the same function-signature line, allowing one deduplicated graph edge
    to evidence identity without pretending its context is return-specific.
    """
    if not isinstance(scope, (ast.FunctionDef, ast.AsyncFunctionDef)):
        return False
    parameter_annotations = [
        arg.annotation
        for arg in [
            *scope.args.posonlyargs, *scope.args.args, *scope.args.kwonlyargs,
            *([scope.args.vararg] if scope.args.vararg else []),
            *([scope.args.kwarg] if scope.args.kwarg else []),
        ]
        if arg.annotation is not None
    ]
    parameter_match = any(
        isinstance(annotation, ast.Name)
        and annotation.id == local_name
        and annotation.lineno == line
        for annotation in parameter_annotations
    )
    return_match = (
        isinstance(scope.returns, ast.Name)
        and scope.returns.id == local_name
        and scope.returns.lineno == line
    )
    return parameter_match and return_match


def _candidate(raw: dict[str, Any]) -> dict[str, Any]:
    candidate = copy.deepcopy(raw)
    edge_key = "edges" if isinstance(candidate.get("edges"), list) else "links"
    candidate[edge_key] = [
        edge for edge in candidate.get(edge_key, [])
        if isinstance(edge, dict) and edge.get("confidence") == "EXTRACTED"
    ]
    return candidate


def validate_graph(graph: dict[str, Any], scan_root: Path, baseline: dict[str, Any]):
    errors, warnings = [], []
    expected_files = baseline.get("source_files", [])
    if not isinstance(expected_files, list) or not expected_files:
        return {"status": "FAIL", "errors": ["baseline source_files must be a non-empty list"]}, None
    try:
        scan_root, source_data, trees, modules, module_to_file = _load_corpus(scan_root, expected_files)
    except (OSError, UnicodeError, SyntaxError, ValueError) as exc:
        return {"status": "FAIL", "errors": [str(exc)]}, None

    declarations, declarations_by_file = _declarations(trees, modules)
    imports, import_errors = _collect_imports(trees, modules, module_to_file, declarations)
    errors.extend(import_errors)

    nodes = graph.get("nodes")
    edges = graph.get("edges") if "edges" in graph else graph.get("links")
    if not isinstance(nodes, list) or not isinstance(edges, list):
        return {"status": "FAIL", "errors": ["graph must have nodes and edges/links arrays"]}, None

    node_by_id, node_source = {}, {}
    source_node_counts = collections.Counter()
    source_line_counts = {key: len(value.splitlines()) for key, value in source_data.items()}
    unanchored_external_nodes = []
    for index, node in enumerate(nodes):
        if not isinstance(node, dict):
            errors.append(f"node {index} is not an object")
            continue
        node_id = node.get("id")
        if not isinstance(node_id, str) or not node_id:
            errors.append(f"node {index} has missing/invalid id")
            continue
        if node_id in node_by_id:
            errors.append(f"duplicate node id: {node_id}")
            continue
        node_by_id[node_id] = node
        relative = _normalize_source(node.get("source_file"), scan_root)
        node_source[node_id] = relative
        if relative is None:
            if node.get("source_file") in ("", None):
                unanchored_external_nodes.append(node_id)
            else:
                errors.append(f"node {node_id} has source path outside the approved scan root")
            continue
        if relative not in source_data:
            errors.append(f"node {node_id} references non-allowlisted source file: {relative}")
            continue
        source_node_counts[relative] += 1
        line = node.get("source_location")
        if not isinstance(line, str) or not line.startswith("L") or not line[1:].isdigit():
            errors.append(f"node {node_id} has invalid source_location")
        elif int(line[1:]) > source_line_counts[relative]:
            errors.append(f"node {node_id} source line exceeds file length: {relative}:{line}")

    confidence_counts = collections.Counter()
    cross_file_edges = []
    review_edges = []
    for index, edge in enumerate(edges):
        if not isinstance(edge, dict):
            errors.append(f"edge {index} is not an object")
            continue
        source_id, target_id = edge.get("source"), edge.get("target")
        if source_id not in node_by_id:
            errors.append(f"edge {index} source endpoint is unresolved: {source_id!r}")
        if target_id not in node_by_id:
            errors.append(f"edge {index} target endpoint is unresolved: {target_id!r}")
        confidence = edge.get("confidence")
        if confidence not in VALID_CONFIDENCES:
            errors.append(f"edge {index} has invalid confidence: {confidence!r}")
            continue
        confidence_counts[confidence] += 1
        source_file = _normalize_source(edge.get("source_file"), scan_root)
        if source_file not in source_data:
            errors.append(f"edge {index} source_file is outside the approved corpus")
            continue
        line = edge.get("source_location")
        if not isinstance(line, str) or not line.startswith("L") or not line[1:].isdigit():
            errors.append(f"edge {index} has invalid source_location")
        elif int(line[1:]) > source_line_counts[source_file]:
            errors.append(f"edge {index} source line exceeds file length: {source_file}:{line}")
        target_file = node_source.get(target_id)
        if target_file in source_data and target_file != source_file:
            cross_file_edges.append({
                "source": source_file, "source_location": line,
                "target": target_file, "relation": edge.get("relation"),
                "confidence": confidence,
                "source_label": node_by_id.get(source_id, {}).get("label"),
                "target_label": node_by_id.get(target_id, {}).get("label"),
            })
        if confidence in {"INFERRED", "AMBIGUOUS"}:
            review_edges.append({
                "source": source_file, "source_location": line,
                "relation": edge.get("relation"), "confidence": confidence,
                "source_label": node_by_id.get(source_id, {}).get("label"),
                "target_label": node_by_id.get(target_id, {}).get("label"),
            })

    # Every source-declared top-level class/function must map to exactly one graph node.
    canonical_nodes = {}
    for (module, name), found in declarations.items():
        if len(found) != 1:
            errors.append(f"source declaration is ambiguous: {module}.{name} ({len(found)} definitions)")
            continue
        declaration = found[0]
        label = _node_label(name, declaration["kind"])
        matches = _matching_nodes(nodes, declaration["file"], label, declaration["line"], scan_root)
        if len(matches) != 1:
            errors.append(
                f"source declaration does not map to one canonical graph node: "
                f"{declaration['file']}:{label}:L{declaration['line']} (matches={len(matches)})"
            )
            continue
        canonical_nodes[(declaration["file"], name)] = matches[0]

    semantic_links = []
    for imp in imports:
        target = canonical_nodes.get((imp["target_file"], imp["imported_name"]))
        if target is None:
            continue
        importer_tree = trees[imp["importer_file"]]
        parents = _parents(importer_tree)
        for scope in _top_level_scopes(importer_tree):
            refs = _references(scope, imp["local_name"], parents)
            if not refs:
                continue
            source_matches = _matching_nodes(
                nodes, imp["importer_file"], _scope_label(scope), scope.lineno, scan_root
            )
            if len(source_matches) != 1:
                errors.append(
                    f"importing scope has no unique graph node: {imp['importer_file']}:"
                    f"{_scope_label(scope)}:L{scope.lineno}"
                )
                continue
            source_node = source_matches[0]
            for ref in refs:
                record = {
                    "importer_file": imp["importer_file"],
                    "target_file": imp["target_file"],
                    "imported_name": imp["imported_name"],
                    "local_name": imp["local_name"],
                    "source_symbol": _scope_label(scope),
                    "source_node_id": source_node["id"],
                    "target_label": target["label"],
                    "target_node_id": target["id"],
                    "target_definition_line": target["source_location"],
                    "source_line": f"L{ref['line']}",
                    "category": ref["category"],
                    "context": ref["context"],
                    "relation": ref["relation"],
                }
                if ref["relation"] is None:
                    warnings.append({"code": "RUNTIME_BODY_REFERENCE_REVIEW_ONLY", **record})
                    semantic_links.append(record)
                    continue
                match_context = ref["context"]
                context_match_mode = "exact"
                if ref["relation"] == "inherits":
                    # Graphify v0.9.100 records inheritance provenance and
                    # canonical endpoints, but emits no context field.
                    match_context = None
                    context_match_mode = "relation_and_provenance"
                raw_matches = _matching_edges(
                    edges, source_node["id"], target["id"], ref["relation"],
                    imp["importer_file"], ref["line"], match_context
                )
                if (
                    not raw_matches
                    and ref["context"] == "return_type"
                    and _coalesced_parameter_return(scope, imp["local_name"], ref["line"])
                ):
                    # Graphify emitted one parameter_type edge for a signature
                    # whose parameter and return annotations share a source line.
                    # Preserve that limitation as a warning, not as a false claim
                    # that the edge independently identifies return_type.
                    coalesced = _matching_edges(
                        edges, source_node["id"], target["id"], ref["relation"],
                        imp["importer_file"], ref["line"], "parameter_type"
                    )
                    if len(coalesced) == 1:
                        raw_matches = coalesced
                        match_context = "parameter_type"
                        context_match_mode = "coalesced_signature_annotation"
                        warnings.append({
                            "code": "SIGNATURE_ANNOTATION_EDGE_COALESCED",
                            "message": "One EXTRACTED edge represents a same-line parameter and return annotation; return-specific context is not independently encoded.",
                            "source_file": imp["importer_file"],
                            "source_line": f"L{ref['line']}",
                            "target_node_id": target["id"],
                            "observed_edge_context": "parameter_type",
                        })
                if len(raw_matches) != 1:
                    errors.append({
                        "code": "CANONICAL_SEMANTIC_EDGE_NOT_UNIQUE",
                        "match_count": len(raw_matches),
                        **record,
                    })
                record["raw_extracted_edge_matches"] = len(raw_matches)
                record["matched_edge_context"] = match_context
                record["context_match_mode"] = context_match_mode
                semantic_links.append(record)

    # Same-label declarations in different packages must stay distinct and imports
    # must point to the exact source file selected by the module path.
    duplicate_labels = collections.defaultdict(set)
    for (source_file, name), node in canonical_nodes.items():
        duplicate_labels[name].add((source_file, node["id"]))
    same_named_groups = {
        name: sorted(files) for name, files in duplicate_labels.items() if len(files) > 1
    }
    for name, entries in same_named_groups.items():
        if len({node_id for _, node_id in entries}) != len(entries):
            errors.append(f"same-named definitions do not have distinct canonical IDs: {name}")

    # Check the specific Phase 02.7 coverage matrix, including relative/absolute
    # imports, duplicated Widget names, type references, function/class calls and
    # single-/multi-base inheritance.
    expected_matrix = baseline.get("coverage_matrix", [])
    matrix_results = []
    for expected in expected_matrix:
        found = [
            link for link in semantic_links
            if link["importer_file"] == expected.get("importer_file")
            and link["imported_name"] == expected.get("imported_name")
            and link["target_file"] == expected.get("target_file")
            and link["category"] == expected.get("category")
            and (expected.get("relation") is None or link["relation"] == expected.get("relation"))
        ]
        ok = bool(found)
        matrix_results.append({"case": expected, "match_count": len(found), "status": "PASS" if ok else "FAIL"})
        if not ok:
            errors.append({"code": "COVERAGE_MATRIX_CASE_MISSING", "case": expected})

    if not cross_file_edges:
        errors.append("no cross-file graph edges were generated")
    if not any(value == "EXTRACTED" for value in confidence_counts):
        errors.append("raw graph contains no EXTRACTED edges")
    represented = sorted(path for path, count in source_node_counts.items() if count)
    declaration_source_files = {
        declaration["file"]
        for found in declarations.values()
        for declaration in found
    }
    missing_declaration_files = sorted(declaration_source_files - set(represented))
    if missing_declaration_files:
        errors.append(
            "source files containing top-level declarations lack graph nodes: "
            + ", ".join(missing_declaration_files)
        )
    if not unanchored_external_nodes:
        warnings.append("no unanchored external nodes were emitted; this is not a failure")

    candidate = _candidate(graph)
    candidate_edges = candidate.get("edges") if "edges" in candidate else candidate.get("links")
    if any(edge.get("confidence") != "EXTRACTED" for edge in candidate_edges if isinstance(edge, dict)):
        errors.append("candidate contains non-EXTRACTED edges")
    if candidate.get("nodes") != nodes:
        errors.append("candidate node records differ from immutable raw graph nodes")

    candidate_semantics = []
    for link in semantic_links:
        if link["relation"] is None:
            continue
        if link.get("raw_extracted_edge_matches") != 1:
            continue
        match = _matching_edges(
            candidate_edges, link["source_node_id"], link["target_node_id"],
            link["relation"], link["importer_file"], int(link["source_line"][1:]),
            link.get("matched_edge_context", link["context"])
        )
        if len(match) != 1:
            errors.append({
                "code": "CANDIDATE_CANONICAL_EDGE_NOT_UNIQUE",
                "match_count": len(match),
                "imported_name": link["imported_name"],
                "relation": link["relation"],
                "source_line": link["source_line"],
            })
        candidate_semantics.append({**link, "candidate_extracted_edge_matches": len(match)})

    raw_sha = _sha(_json_bytes(graph))
    candidate_sha = _sha(_json_bytes(candidate))
    summary = {
        "schema_version": "1.0.0",
        "phase": "02.7",
        "baseline_id": baseline.get("baseline_id"),
        "status": "FAIL" if errors else "PASS_WITH_WARNINGS" if warnings else "PASS",
        "semantic_context_fidelity": "PARTIAL_WITH_WARNINGS" if any(isinstance(w, dict) and w.get("code") == "SIGNATURE_ANNOTATION_EDGE_COALESCED" for w in warnings) else "VERIFIED",
        "errors": errors,
        "warnings": warnings,
        "raw_graph": {
            "sha256_canonical_json": raw_sha,
            "node_count": len(nodes),
            "edge_count": len(edges),
            "confidence_counts": dict(confidence_counts),
            "represented_source_files": represented,
            "cross_file_edge_count": len(cross_file_edges),
            "unanchored_external_node_count": len(unanchored_external_nodes),
            "cross_file_edges": cross_file_edges,
            "review_edges": review_edges,
        },
        "candidate_graph": {
            "sha256_canonical_json": candidate_sha,
            "node_count": len(candidate.get("nodes", [])),
            "edge_count": len(candidate_edges),
            "confidence_counts": dict(collections.Counter(
                edge.get("confidence") for edge in candidate_edges if isinstance(edge, dict)
            )),
            "contains_non_extracted_edges": any(
                edge.get("confidence") != "EXTRACTED" for edge in candidate_edges if isinstance(edge, dict)
            ),
        },
        "import_resolutions": imports,
        "canonical_semantic_links": semantic_links,
        "candidate_semantic_links": candidate_semantics,
        "same_named_definition_groups": same_named_groups,
        "coverage_matrix": matrix_results,
        "governance": {
            "raw_graph_mutated": False,
            "candidate_graph_is_separate": True,
            "candidate_contains_only_extracted_edges": True,
            "inferred_edges_promoted": False,
            "ambiguous_edges_promoted": False,
            "graphify_execution_count_authorized": 1,
            "model_credentials_present": False,
            "production_promotion": "NOT_AUTHORIZED",
            "oia_runtime_integration": "NOT_AUTHORIZED",
        },
        "source_file_sha256": {
            relative: _sha(text.encode("utf-8")) for relative, text in sorted(source_data.items())
        },
    }
    return summary, candidate


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--graph", required=True, type=Path)
    parser.add_argument("--scan-root", required=True, type=Path)
    parser.add_argument("--baseline", required=True, type=Path)
    parser.add_argument("--candidate-out", required=True, type=Path)
    parser.add_argument("--summary-out", required=True, type=Path)
    args = parser.parse_args()
    try:
        graph = json.loads(args.graph.read_text(encoding="utf-8"))
        baseline = json.loads(args.baseline.read_text(encoding="utf-8"))
        summary, candidate = validate_graph(graph, args.scan_root, baseline)
        if candidate is not None:
            args.candidate_out.parent.mkdir(parents=True, exist_ok=True)
            args.candidate_out.write_text(json.dumps(candidate, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        summary = {"schema_version": "1.0.0", "phase": "02.7", "status": "FAIL", "errors": [str(exc)]}
    args.summary_out.parent.mkdir(parents=True, exist_ok=True)
    args.summary_out.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Phase 02.7 compatibility matrix: {summary.get('status')}")
    print(f"Raw nodes/edges: {summary.get('raw_graph', {}).get('node_count', 0)}/{summary.get('raw_graph', {}).get('edge_count', 0)}")
    print(f"Cross-file edges: {summary.get('raw_graph', {}).get('cross_file_edge_count', 0)}")
    print(f"Coverage matrix: {sum(1 for item in summary.get('coverage_matrix', []) if item.get('status') == 'PASS')}/{len(summary.get('coverage_matrix', []))}")
    print("Inferred/ambiguous promotion: NOT AUTHORIZED")
    for error in summary.get("errors", []):
        print(f"FAIL: {error}")
    return 0 if summary.get("status") in {"PASS", "PASS_WITH_WARNINGS"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
