#!/usr/bin/env python3
"""Read-only cross-file canonical identity and semantic-edge validator.

Uses Python's stdlib AST as an independent source oracle. It never executes
Graphify and never rewrites raw or candidate graph data.
"""
from __future__ import annotations

import argparse
import ast
import collections
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
from typing import Any

ALLOWED = {"src/contract_guard.py", "src/outfit_flow.py"}
EDGE_ID_FIELDS = ("source", "target", "relation", "confidence", "source_file", "source_location")


def _canonical_json(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _edge_identity(edge: dict[str, Any]) -> dict[str, Any]:
    return {key: edge.get(key) for key in EDGE_ID_FIELDS}


def _edge_fingerprint(edge: dict[str, Any]) -> str:
    return _sha(_canonical_json(_edge_identity(edge)))


def _read_sources(root: Path):
    root = root.resolve()
    result = {}
    for rel in sorted(ALLOWED):
        path = root / rel
        if not path.is_file() or path.is_symlink() or root not in path.resolve().parents:
            raise ValueError(f"missing/unsafe approved source fixture: {rel}")
        text = path.read_text(encoding="utf-8")
        result[rel] = (text, ast.parse(text, filename=rel))
    return result


def _module_target(importer: str, module: str, sources: dict) -> str | None:
    """Resolve only imports whose target is one of the explicitly allowlisted files."""
    importer_parent = PurePosixPath(importer).parent
    rel_candidate = (importer_parent / (module.replace(".", "/") + ".py")).as_posix()
    if rel_candidate in sources:
        return rel_candidate
    direct = f"src/{module.replace('.', '/')}.py"
    if direct in sources:
        return direct
    stem_matches = [p for p in sources if PurePosixPath(p).stem == module.split(".")[-1]]
    return stem_matches[0] if len(stem_matches) == 1 else None


def _definitions(sources: dict):
    found = collections.defaultdict(list)
    for rel, (_, tree) in sources.items():
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                found[(rel, node.name)].append(("class", node.lineno, node))
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                found[(rel, node.name)].append(("function", node.lineno, node))
    return found


def _parents(tree: ast.AST):
    parents = {}
    for parent in ast.walk(tree):
        for child in ast.iter_child_nodes(parent):
            parents[child] = parent
    return parents


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
    if isinstance(scope, ast.ClassDef):
        return scope.name
    return f"{scope.name}()"


def _annotation_roots(scope: ast.AST):
    roots: list[tuple[ast.AST, str]] = []
    if isinstance(scope, (ast.FunctionDef, ast.AsyncFunctionDef)):
        args = [
            *scope.args.posonlyargs, *scope.args.args, *scope.args.kwonlyargs
        ]
        if scope.args.vararg:
            args.append(scope.args.vararg)
        if scope.args.kwarg:
            args.append(scope.args.kwarg)
        roots.extend((arg.annotation, "parameter_type") for arg in args if arg.annotation is not None)
        if scope.returns is not None:
            roots.append((scope.returns, "return_type"))
    for node in ast.walk(scope):
        if isinstance(node, ast.AnnAssign):
            roots.append((node.annotation, "variable_type"))
    return roots


def _class_base_roots(scope: ast.AST):
    return list(scope.bases) if isinstance(scope, ast.ClassDef) else []


def _source_scopes(tree: ast.AST):
    return [
        node for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
    ]


def _node_for_scope(graph_nodes: list[dict], source_file: str, scope: ast.AST):
    label = _scope_label(scope)
    matches = [
        node for node in graph_nodes
        if isinstance(node, dict)
        and node.get("file_type") == "code"
        and node.get("source_file") == source_file
        and node.get("source_location") == f"L{scope.lineno}"
        and node.get("label") == label
    ]
    return matches


def _canonical_node(graph_nodes: list[dict], source_file: str, symbol: str, line: int, kind: str):
    matches = [
        node for node in graph_nodes
        if isinstance(node, dict)
        and node.get("file_type") == "code"
        and node.get("source_file") == source_file
        and node.get("source_location") == f"L{line}"
        and node.get("label") == (f"{symbol}()" if kind == "function" else symbol)
        and (node.get("_callable") is True)
        and (node.get("_callable_class") is True if kind == "class" else node.get("_callable_class") is not True)
    ]
    return matches


def _collect_imports(sources: dict, definitions: dict):
    imports, errors = [], []
    for rel, (_, tree) in sources.items():
        for node in ast.walk(tree):
            if not isinstance(node, ast.ImportFrom) or not node.module:
                continue
            target_file = _module_target(rel, node.module, sources)
            if target_file is None:
                continue  # external/out-of-scope import
            for alias in node.names:
                imported_name = alias.name
                local_name = alias.asname or alias.name
                declarations = definitions.get((target_file, imported_name), [])
                if len(declarations) != 1:
                    errors.append({
                        "code": "INTERNAL_IMPORT_NOT_UNIQUELY_RESOLVED",
                        "source_file": rel,
                        "source_location": f"L{node.lineno}",
                        "module": node.module,
                        "imported_name": imported_name,
                        "target_file": target_file,
                        "declaration_count": len(declarations),
                    })
                    continue
                kind, line, _ = declarations[0]
                imports.append({
                    "source_file": rel,
                    "import_line": node.lineno,
                    "module": node.module,
                    "imported_name": imported_name,
                    "local_name": local_name,
                    "target_file": target_file,
                    "target_line": line,
                    "target_kind": kind,
                })
    return imports, errors


def _references_for_scope(scope: ast.AST, local_name: str, parents: dict):
    annotation_roots = _annotation_roots(scope)
    base_roots = _class_base_roots(scope)
    refs = []
    for node in ast.walk(scope):
        if not isinstance(node, ast.Name) or node.id != local_name or not isinstance(node.ctx, ast.Load):
            continue
        if _nearest_scope(node, parents) is not scope:
            continue
        annotation_kind = next(
            (kind for root, kind in annotation_roots if _within(node, root, parents)),
            None,
        )
        if annotation_kind:
            category, context = "TYPE_ANNOTATION", annotation_kind
        elif any(_within(node, base, parents) for base in base_roots):
            category, context = "CLASS_BASE", "base"
        else:
            parent = parents.get(node)
            if isinstance(parent, ast.Call) and parent.func is node:
                category, context = "RUNTIME_CALL", "call"
            else:
                category, context = "RUNTIME_BODY_REFERENCE", None
        refs.append({
            "line": node.lineno,
            "column": node.col_offset,
            "category": category,
            "context": context,
            "local_name": local_name,
        })
    return sorted(refs, key=lambda x: (x["line"], x["column"]))


def _expected_relation(ref: dict):
    return {
        "TYPE_ANNOTATION": "references",
        "RUNTIME_CALL": "calls",
        "CLASS_BASE": "inherits",
    }.get(ref["category"])


def _find_edges(edges: list[dict], source_id: str, target_id: str, relation: str, source_file: str, line: int, context: str | None):
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


def validate(raw_graph: dict, candidate_graph: dict, manifest: dict, graph_baseline: dict, semantic_baseline: dict, scan_root: Path):
    errors, warnings = [], []
    sources = _read_sources(scan_root)
    definitions = _definitions(sources)
    imports, import_errors = _collect_imports(sources, definitions)
    errors.extend(import_errors)

    raw_nodes, candidate_nodes = raw_graph.get("nodes", []), candidate_graph.get("nodes", [])
    raw_edges, candidate_edges = raw_graph.get("edges", []), candidate_graph.get("edges", [])
    if not all(isinstance(x, list) for x in (raw_nodes, candidate_nodes, raw_edges, candidate_edges)):
        return {"schema_version": "1.0.0", "phase": "02.6", "status": "FAIL", "errors": ["raw/candidate nodes and edges must be arrays"]}

    # Graphs must still be exactly the pinned pair from Phase 02.5.
    raw_sha = _sha(_canonical_json(raw_graph))
    # Compare byte-level graph hashes in the CLI as well; here use graph_baseline
    # for semantic identity/provenance and compare the imported graph records.
    expected_graphs = graph_baseline.get("graphs", {})
    if raw_graph.get("_raw_sha256") is not None and raw_graph.get("_raw_sha256") != expected_graphs.get("raw_sha256"):
        errors.append("raw graph identity differs from Phase 02.5 evidence baseline")
    if semantic_baseline.get("graphify", {}).get("source_commit") != graph_baseline.get("graphify", {}).get("source_commit"):
        errors.append("Graphify source pin differs between semantic and graph integrity baselines")

    canonical_index = {}
    for imp in imports:
        candidates = _canonical_node(raw_nodes, imp["target_file"], imp["imported_name"], imp["target_line"], imp["target_kind"])
        if len(candidates) != 1:
            errors.append({
                "code": "CANONICAL_TARGET_NODE_NOT_UNIQUE",
                "source_file": imp["source_file"],
                "imported_name": imp["imported_name"],
                "target_file": imp["target_file"],
                "expected_source_line": imp["target_line"],
                "candidate_count": len(candidates),
            })
            continue
        canonical_index[(imp["source_file"], imp["local_name"])] = candidates[0]

    semantic_edges = []
    for rel, (_, tree) in sources.items():
        parents = _parents(tree)
        for scope in _source_scopes(tree):
            source_nodes = _node_for_scope(raw_nodes, rel, scope)
            if len(source_nodes) != 1:
                # Only insist on graph nodes for scopes that reference an imported
                # internal name; check after collecting references.
                source_node = None
            else:
                source_node = source_nodes[0]
            for (import_file, local_name), target_node in canonical_index.items():
                if import_file != rel:
                    continue
                refs = _references_for_scope(scope, local_name, parents)
                if not refs:
                    continue
                if source_node is None:
                    errors.append({
                        "code": "SOURCE_SCOPE_NODE_NOT_UNIQUE",
                        "source_file": rel,
                        "scope": _scope_label(scope),
                        "line": scope.lineno,
                        "candidate_count": len(source_nodes),
                    })
                    continue
                for ref in refs:
                    record = {
                        "source_symbol": _scope_label(scope),
                        "source_node_id": source_node["id"],
                        "source_file": rel,
                        "source_line": ref["line"],
                        "imported_name": next(
                            item["imported_name"] for item in imports
                            if item["source_file"] == rel and item["local_name"] == local_name
                        ),
                        "local_name": local_name,
                        "target_symbol": target_node["label"],
                        "target_node_id": target_node["id"],
                        "target_file": target_node["source_file"],
                        "target_definition_line": target_node["source_location"],
                        "category": ref["category"],
                        "context": ref["context"],
                    }
                    relation = _expected_relation(ref)
                    if relation:
                        raw_matches = _find_edges(raw_edges, source_node["id"], target_node["id"], relation, rel, ref["line"], ref["context"])
                        candidate_matches = _find_edges(candidate_edges, source_node["id"], target_node["id"], relation, rel, ref["line"], ref["context"])
                        record["relation"] = relation
                        record["raw_extracted_edge_matches"] = len(raw_matches)
                        record["candidate_extracted_edge_matches"] = len(candidate_matches)
                        if len(raw_matches) != 1:
                            errors.append({"code": "RAW_SEMANTIC_EDGE_MISSING_OR_DUPLICATED", **record})
                        if len(candidate_matches) != 1:
                            errors.append({"code": "CANDIDATE_SEMANTIC_EDGE_MISSING_OR_DUPLICATED", **record})
                    else:
                        record["review_only"] = True
                        warnings.append({
                            "code": "IMPORTED_NAME_RUNTIME_BODY_REFERENCE_REQUIRES_RELATION_REVIEW",
                            **record,
                        })
                    semantic_edges.append(record)

    # Every versioned semantic expectation must be present in the source-derived
    # relationships. This prevents replacing an expected internal import with an
    # external import (or deleting the reference) from silently passing.
    for expected in semantic_baseline.get("semantic_expectations", []):
        matches = [
            item for item in semantic_edges
            if item.get("source_symbol") == expected.get("source_symbol")
            and item.get("imported_name") == expected.get("imported_name")
            and item.get("category") == expected.get("category")
            and item.get("relation") == expected.get("relation")
            and item.get("source_file") == expected.get("source_file")
            and item.get("source_line") == int(str(expected.get("source_location", "L0")).removeprefix("L"))
            and item.get("target_file") == expected.get("target_file")
            and item.get("target_symbol") == expected.get("target_symbol")
            and item.get("target_definition_line") == expected.get("target_definition")
            and item.get("context") == expected.get("context")
        ]
        if len(matches) != 1:
            errors.append({
                "code": "VERSIONED_SEMANTIC_EXPECTATION_MISSING_OR_NONUNIQUE",
                "expected": expected,
                "match_count": len(matches),
            })

    # The held INFERRED uses edge must still be present in raw, absent from the
    # candidate, and backed by the exact owner-confirmed manifest decision.
    held = semantic_baseline.get("held_edge", {})
    held_source = held.get("source_node_id")
    held_target = held.get("target_node_id")
    held_line = held.get("source_location")
    held_edge = [
        e for e in raw_edges if isinstance(e, dict)
        and e.get("source") == held_source and e.get("target") == held_target
        and e.get("relation") == "uses" and e.get("confidence") == "INFERRED"
        and e.get("source_file") == held.get("source_file")
        and e.get("source_location") == held_line
    ]
    candidate_held = [
        e for e in candidate_edges if isinstance(e, dict)
        and e.get("source") == held_source and e.get("target") == held_target
        and e.get("relation") == "uses" and e.get("confidence") == "INFERRED"
    ]
    fingerprints = {d.get("edge_fingerprint"): d for d in manifest.get("edge_decisions", []) if isinstance(d, dict)}
    decision = fingerprints.get(_edge_fingerprint(held_edge[0])) if len(held_edge) == 1 else None
    if len(held_edge) != 1 or decision is None or decision.get("owner_confirmation") != "CONFIRMED_HOLD" or decision.get("disposition") != "HOLD_NOT_PROMOTED":
        errors.append({"code": "HELD_INFERRED_EDGE_OR_OWNER_DECISION_NOT_PRESERVED", "raw_matches": len(held_edge)})
    if candidate_held:
        errors.append({"code": "HELD_INFERRED_EDGE_LEAKED_INTO_CANDIDATE", "candidate_matches": len(candidate_held)})

    # Explicitly detect duplicate source definitions for imported targets.
    for imp in imports:
        defs = definitions.get((imp["target_file"], imp["imported_name"]), [])
        if len(defs) != 1:
            continue
        ghost_like = [
            n for n in raw_nodes
            if isinstance(n, dict) and n.get("file_type") == "code"
            and n.get("label") == imp["imported_name"]
            and n.get("source_file") == imp["target_file"]
            and n.get("source_location") != f"L{imp['target_line']}"
        ]
        if ghost_like:
            errors.append({
                "code": "NONCANONICAL_SHADOW_NODE_FOR_IMPORTED_SYMBOL",
                "imported_name": imp["imported_name"],
                "target_file": imp["target_file"],
                "shadow_node_ids": [n.get("id") for n in ghost_like],
            })

    # Validate the declared v0.9.100 upstream regression coverage for this scope.
    upstream_tests = semantic_baseline.get("upstream_regression_tests", [])
    if not upstream_tests:
        errors.append("semantic baseline lacks pinned upstream regression test references")

    return {
        "schema_version": "1.0.0",
        "phase": "02.6",
        "baseline_id": semantic_baseline.get("baseline_id"),
        "status": "PASS" if not errors else "FAIL",
        "errors": errors,
        "warnings": warnings,
        "graphify": semantic_baseline.get("graphify"),
        "imports_resolved": imports,
        "canonical_import_targets": [
            {
                "source_file": source_file,
                "local_name": local_name,
                "node_id": node.get("id"),
                "label": node.get("label"),
                "source_file_target": node.get("source_file"),
                "source_location": node.get("source_location"),
            }
            for (source_file, local_name), node in sorted(canonical_index.items())
        ],
        "semantic_edges": semantic_edges,
        "held_edge": {
            "raw_present": len(held_edge) == 1,
            "candidate_present": bool(candidate_held),
            "owner_confirmation": decision.get("owner_confirmation") if decision else None,
            "promotion": "NOT_AUTHORIZED",
        },
        "governance": {
            "owner_disposition": "CONFIRMED_HOLD",
            "inferred_edge_promoted": False,
            "raw_graph_mutated": False,
            "candidate_graph_mutated": False,
            "graphify_execution_performed": False,
            "production_promotion": "NOT_AUTHORIZED",
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-graph", required=True, type=Path)
    parser.add_argument("--candidate-graph", required=True, type=Path)
    parser.add_argument("--decision-manifest", required=True, type=Path)
    parser.add_argument("--graph-evidence-baseline", required=True, type=Path)
    parser.add_argument("--semantic-baseline", required=True, type=Path)
    parser.add_argument("--scan-root", required=True, type=Path)
    parser.add_argument("--report-out", required=True, type=Path)
    args = parser.parse_args()
    try:
        raw_bytes = args.raw_graph.read_bytes()
        candidate_bytes = args.candidate_graph.read_bytes()
        raw_sha, candidate_sha = _sha(raw_bytes), _sha(candidate_bytes)
        raw = json.loads(raw_bytes)
        candidate = json.loads(candidate_bytes)
        manifest = json.loads(args.decision_manifest.read_text(encoding="utf-8"))
        graph_baseline = json.loads(args.graph_evidence_baseline.read_text(encoding="utf-8"))
        semantic_baseline = json.loads(args.semantic_baseline.read_text(encoding="utf-8"))
        report = validate(raw, candidate, manifest, graph_baseline, semantic_baseline, args.scan_root)
        if raw_sha != graph_baseline.get("graphs", {}).get("raw_sha256"):
            report["errors"].append("raw graph byte SHA-256 differs from pinned Phase 02.5 baseline")
        if candidate_sha != graph_baseline.get("graphs", {}).get("candidate_sha256"):
            report["errors"].append("candidate graph byte SHA-256 differs from pinned Phase 02.5 baseline")
        report["status"] = "PASS" if not report["errors"] else "FAIL"
        report["input_hashes"] = {"raw_graph_sha256": raw_sha, "candidate_graph_sha256": candidate_sha}
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        report = {"schema_version": "1.0.0", "phase": "02.6", "status": "FAIL", "errors": [str(exc)]}
    report["run_context"] = {
        "commit": os.getenv("GITHUB_SHA"),
        "run_id": os.getenv("GITHUB_RUN_ID"),
        "run_attempt": os.getenv("GITHUB_RUN_ATTEMPT"),
    }
    args.report_out.parent.mkdir(parents=True, exist_ok=True)
    args.report_out.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Phase 02.6 canonical semantic validation: {report['status']}")
    print(f"Resolved internal imports: {len(report.get('imports_resolved', []))}")
    print(f"Validated semantic references: {len(report.get('semantic_edges', []))}")
    print("Graphify extraction performed: NO; promotion authorized: NO")
    for error in report.get("errors", []):
        print(f"FAIL: {error}")
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
