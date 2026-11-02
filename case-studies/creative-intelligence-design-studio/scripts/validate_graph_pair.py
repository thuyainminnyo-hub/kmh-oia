#!/usr/bin/env python3
"""Read-only integrity comparison for the pinned Graphify raw/candidate graphs."""
from __future__ import annotations

import argparse
import ast
import collections
import hashlib
import json
import os
import re
from pathlib import Path, PurePosixPath
from typing import Any

ALLOWED = {"src/contract_guard.py", "src/outfit_flow.py"}
CONFIDENCES = {"EXTRACTED", "INFERRED", "AMBIGUOUS"}
EDGE_FIELDS = ("source", "target", "relation", "confidence", "source_file", "source_location")


def _json(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _edge_id(edge: dict[str, Any]) -> dict[str, Any]:
    return {key: edge.get(key) for key in EDGE_FIELDS}


def _fingerprint(edge: dict[str, Any]) -> str:
    return _sha(_json(_edge_id(edge)))


def _path(value: Any) -> str | None:
    if not isinstance(value, str) or not value or "\\" in value:
        return None
    p = PurePosixPath(value)
    if p.is_absolute() or ".." in p.parts or "." in p.parts or p.as_posix() != value:
        return None
    return value


def _line(value: Any) -> int | None:
    if not isinstance(value, str) or not re.fullmatch(r"L[1-9][0-9]*", value):
        return None
    return int(value[1:])


def _source_context(root: Path):
    lines, trees = {}, {}
    root = root.resolve()
    for rel in sorted(ALLOWED):
        p = root / rel
        if not p.is_file() or p.is_symlink() or root not in p.resolve().parents:
            raise ValueError(f"missing/unsafe source fixture: {rel}")
        text = p.read_text(encoding="utf-8")
        lines[rel] = text.splitlines()
        trees[rel] = ast.parse(text, filename=rel)
    return lines, trees


def _docstrings(tree: ast.Module):
    result = set()
    for node in ast.walk(tree):
        body = getattr(node, "body", None)
        if isinstance(body, list) and body:
            first = body[0]
            if isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant) and isinstance(first.value.value, str):
                result.add((first.value.lineno, first.value.value))
    return result


def _symbol_error(node: dict[str, Any], tree: ast.Module, source: str, line: int):
    label, kind = node.get("label"), node.get("file_type")
    if not isinstance(label, str) or not label:
        return "missing label"
    if kind == "rationale":
        return None if (line, label) in _docstrings(tree) else "rationale does not match source docstring"
    if kind != "code":
        return None
    if label == PurePosixPath(source).name and not node.get("_callable"):
        return None if line == 1 else "file node not anchored at L1"
    if node.get("_callable_class"):
        ok = any(isinstance(x, ast.ClassDef) and x.name == label and x.lineno == line for x in ast.walk(tree))
        return None if ok else "class definition not found at source anchor"
    if node.get("_callable"):
        name = label[:-2] if label.endswith("()") else None
        ok = bool(name) and any(isinstance(x, (ast.FunctionDef, ast.AsyncFunctionDef)) and x.name == name and x.lineno == line for x in ast.walk(tree))
        return None if ok else "function definition not found at source anchor"
    return "unrecognized code-node identity"


def _inspect(graph: dict[str, Any], name: str, lines: dict, trees: dict):
    errors, warnings = [], []
    nodes, edges = graph.get("nodes"), graph.get("edges")
    if not isinstance(nodes, list) or not isinstance(edges, list):
        return {"errors": [f"{name}: nodes/edges must be arrays"]}
    by_id, sources, signatures = {}, {}, collections.Counter()
    external, ghost = [], []
    for i, n in enumerate(nodes):
        if not isinstance(n, dict) or not isinstance(n.get("id"), str) or not n["id"]:
            errors.append(f"{name}: invalid node at index {i}"); continue
        nid = n["id"]
        if nid in by_id:
            errors.append(f"{name}: duplicate node id {nid}"); continue
        by_id[nid] = n
        if n.get("external") is True:
            if n.get("source_file") not in (None, ""):
                errors.append(f"{name}: external node {nid} has source_file")
            external.append(nid); sources[nid] = None; continue
        src = _path(n.get("source_file"))
        if src not in ALLOWED:
            errors.append(f"{name}: {nid} has non-allowlisted source_file"); sources[nid] = None; continue
        sources[nid] = src
        ln = _line(n.get("source_location"))
        if ln is None or ln > len(lines[src]):
            errors.append(f"{name}: {nid} has invalid/out-of-range source anchor"); ghost.append(nid); continue
        problem = _symbol_error(n, trees[src], src, ln)
        if problem:
            errors.append(f"{name}: {nid}: {problem}"); ghost.append(nid)
        signatures[(src, n.get("source_location"), n.get("file_type"), n.get("label"))] += 1
    dup_nodes = sum(1 for v in signatures.values() if v > 1)
    if dup_nodes:
        errors.append(f"{name}: {dup_nodes} duplicate canonical node signature(s)")

    degrees, edge_sigs, conf = collections.Counter(), collections.Counter(), collections.Counter()
    cross, non_extracted = 0, []
    for i, e in enumerate(edges):
        if not isinstance(e, dict):
            errors.append(f"{name}: invalid edge at index {i}"); continue
        s, t = e.get("source"), e.get("target")
        if s not in by_id: errors.append(f"{name}: unresolved source endpoint {s!r}")
        if t not in by_id: errors.append(f"{name}: unresolved target endpoint {t!r}")
        if s in by_id: degrees[s] += 1
        if t in by_id: degrees[t] += 1
        c = e.get("confidence")
        if c not in CONFIDENCES: errors.append(f"{name}: invalid confidence {c!r}")
        else:
            conf[c] += 1
            if c != "EXTRACTED": non_extracted.append(e)
        if not isinstance(e.get("relation"), str) or not e["relation"]:
            errors.append(f"{name}: edge {i} has no relation")
        src = _path(e.get("source_file")); ln = _line(e.get("source_location"))
        if src not in ALLOWED or ln is None or ln > len(lines.get(src, [])):
            errors.append(f"{name}: edge {i} has invalid source anchor")
        edge_identity = {**_edge_id(e), "context": e.get("context")}
        edge_sigs[_json(edge_identity)] += 1
        sp, tp = sources.get(s), sources.get(t)
        if sp and tp and sp != tp: cross += 1
    dup_edges = sum(1 for v in edge_sigs.values() if v > 1)
    if dup_edges: errors.append(f"{name}: {dup_edges} exact duplicate edge identity/identities")
    isolated = sorted(nid for nid in by_id if degrees[nid] == 0 and by_id[nid].get("external") is not True)
    if isolated: warnings.append(f"{name}: isolated source-backed nodes: {isolated}")
    return {
        "status": "PASS" if not errors else "FAIL", "errors": errors, "warnings": warnings,
        "node_count": len(nodes), "edge_count": len(edges), "confidence_counts": dict(conf),
        "source_backed_nodes": len(sources) - len(external), "external_node_ids": sorted(external),
        "unresolved_endpoint_count": sum("unresolved" in e for e in errors),
        "duplicate_node_id_count": sum("duplicate node id" in e for e in errors),
        "duplicate_canonical_node_signature_count": dup_nodes, "duplicate_edge_identity_count": dup_edges,
        "ghost_node_indicator_count": len(ghost), "ghost_node_indicators": ghost,
        "isolated_source_backed_node_ids": isolated, "internal_cross_file_edge_count": cross,
        "non_extracted_edges": [_edge_id(e) for e in non_extracted],
    }


def validate(raw_bytes: bytes, candidate_bytes: bytes, decision: dict, promotion: dict, root: Path, baseline: dict):
    errors = []
    raw_sha, candidate_sha = _sha(raw_bytes), _sha(candidate_bytes)
    try:
        raw, candidate = json.loads(raw_bytes), json.loads(candidate_bytes)
    except json.JSONDecodeError as exc:
        raise ValueError(f"graph JSON parse failed: {exc}") from exc
    if not isinstance(raw, dict) or not isinstance(candidate, dict):
        raise ValueError("raw/candidate graph must be JSON objects")
    src = decision.get("source_artifact", {})
    if raw_sha != src.get("graph_sha256") or raw_sha != promotion.get("raw_graph_sha256") or raw_sha != baseline.get("graphs", {}).get("raw_sha256"):
        errors.append("raw graph SHA-256 does not match pinned manifest/report/baseline")
    if candidate_sha != promotion.get("candidate_graph_sha256") or candidate_sha != baseline.get("graphs", {}).get("candidate_sha256"):
        errors.append("candidate graph SHA-256 does not match pinned report/baseline")
    owner = decision.get("owner_decision", {})
    if decision.get("review_status") != "OWNER_CONFIRMED_HOLD_PENDING_ADDITIONAL_EVIDENCE" or owner.get("decision") != "KEEP_INFERRED_EDGE_UNDER_REVIEW_DO_NOT_PROMOTE" or owner.get("production_promotion") != "NOT_AUTHORIZED":
        errors.append("decision manifest does not preserve owner-confirmed HOLD")
    if promotion.get("owner_confirmation") != "CONFIRMED_HOLD" or promotion.get("production_promotion") != "NOT_AUTHORIZED":
        errors.append("promotion report does not preserve owner-confirmed HOLD / no promotion")
    bs, bg = baseline.get("source_artifact", {}), baseline.get("graphify", {})
    if (bs.get("workflow_run_id"), bs.get("artifact_id")) != (src.get("workflow_run_id"), src.get("artifact_id")):
        errors.append("raw artifact identity does not match versioned baseline")
    if (bg.get("version"), bg.get("source_commit")) != (src.get("graphify_version"), src.get("graphify_source_commit")):
        errors.append("Graphify pin does not match versioned baseline")
    lines, trees = _source_context(root)
    raw_s = _inspect(raw, "raw graph", lines, trees)
    cand_s = _inspect(candidate, "candidate graph", lines, trees)
    errors.extend(raw_s.get("errors", [])); errors.extend(cand_s.get("errors", []))
    rn = {n.get("id"): n for n in raw.get("nodes", []) if isinstance(n, dict)}
    cn = {n.get("id"): n for n in candidate.get("nodes", []) if isinstance(n, dict)}
    parity = set(rn) == set(cn) and all(rn.get(k) == cn.get(k) for k in rn)
    if not parity: errors.append("candidate node records/IDs differ from raw graph")
    extracted = [e for e in raw.get("edges", []) if isinstance(e, dict) and e.get("confidence") == "EXTRACTED"]
    candidate_edges = [e for e in candidate.get("edges", []) if isinstance(e, dict)]
    edges_match = collections.Counter(_json(e) for e in extracted) == collections.Counter(_json(e) for e in candidate_edges)
    if not edges_match: errors.append("candidate is not the exact complete set of raw EXTRACTED edges")
    if any(e.get("confidence") != "EXTRACTED" for e in candidate_edges): errors.append("candidate contains non-EXTRACTED edge")
    non_extracted = [e for e in raw.get("edges", []) if isinstance(e, dict) and e.get("confidence") != "EXTRACTED"]
    decisions = {d.get("edge_fingerprint"): d for d in decision.get("edge_decisions", []) if isinstance(d, dict)}
    observed = set()
    for edge in non_extracted:
        fp = _fingerprint(edge); observed.add(fp); d = decisions.get(fp)
        if d is None or d.get("edge_identity") != _edge_id(edge) or d.get("disposition") != "HOLD_NOT_PROMOTED" or d.get("owner_confirmation") != "CONFIRMED_HOLD":
            errors.append(f"raw non-EXTRACTED edge lacks matching owner-confirmed HOLD decision: {fp}")
    if observed != set(decisions): errors.append("review manifest contains missing or unused non-EXTRACTED decisions")
    actual = {
        "raw": {"nodes": len(raw.get("nodes", [])), "edges": len(raw.get("edges", [])), "confidence": raw_s.get("confidence_counts", {})},
        "candidate": {"nodes": len(candidate.get("nodes", [])), "edges": len(candidate_edges), "confidence": cand_s.get("confidence_counts", {})},
    }
    if actual != {"raw": promotion.get("raw_graph_counts", {}), "candidate": promotion.get("candidate_graph_counts", {})}:
        errors.append("graph counts do not match promotion report")
    if actual != baseline.get("expected_metrics"):
        errors.append("graph counts do not match versioned evidence baseline")
    colocated = collections.defaultdict(set)
    for e in raw.get("edges", []):
        if isinstance(e, dict): colocated[(e.get("source"), e.get("target"), e.get("source_file"), e.get("source_location"))].add(e.get("relation"))
    relation_variants = [
        {"source": k[0], "target": k[1], "source_file": k[2], "source_location": k[3], "relations": sorted(v)}
        for k, v in colocated.items() if len(v) > 1
    ]
    return {
        "schema_version": "1.0.0", "phase": "02.5", "baseline_id": baseline.get("baseline_id"),
        "status": "PASS" if not errors else "FAIL", "errors": errors,
        "inputs": {"raw_graph_sha256": raw_sha, "candidate_graph_sha256": candidate_sha},
        "graphs": {"raw": raw_s, "candidate": cand_s},
        "comparison": {"candidate_node_parity_with_raw": parity, "candidate_edges_equal_all_raw_extracted": edges_match,
                       "held_non_extracted_edges": len(non_extracted), "owner_decisions_match": observed == set(decisions),
                       "co_located_multi_relation_groups_for_review": relation_variants},
        "governance": {"owner_disposition": "CONFIRMED_HOLD", "inferred_edge_promoted": False,
                       "raw_graph_mutated": False, "candidate_graph_mutated": False,
                       "graphify_execution_performed": False, "production_promotion": "NOT_AUTHORIZED"},
    }


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--raw-graph", required=True, type=Path); p.add_argument("--candidate-graph", required=True, type=Path)
    p.add_argument("--decision-manifest", required=True, type=Path); p.add_argument("--promotion-report", required=True, type=Path)
    p.add_argument("--evidence-baseline", required=True, type=Path); p.add_argument("--scan-root", required=True, type=Path)
    p.add_argument("--report-out", required=True, type=Path); a = p.parse_args()
    try:
        report = validate(a.raw_graph.read_bytes(), a.candidate_graph.read_bytes(),
                          json.loads(a.decision_manifest.read_text()), json.loads(a.promotion_report.read_text()),
                          a.scan_root, json.loads(a.evidence_baseline.read_text()))
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        report = {"schema_version": "1.0.0", "phase": "02.5", "status": "FAIL", "errors": [str(exc)]}
    report["run_context"] = {"commit": os.getenv("GITHUB_SHA"), "run_id": os.getenv("GITHUB_RUN_ID"), "run_attempt": os.getenv("GITHUB_RUN_ATTEMPT")}
    a.report_out.parent.mkdir(parents=True, exist_ok=True)
    a.report_out.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Phase 02.5 graph integrity: {report['status']}")
    print(f"Raw SHA-256: {report.get('inputs', {}).get('raw_graph_sha256', 'unavailable')}")
    print(f"Candidate SHA-256: {report.get('inputs', {}).get('candidate_graph_sha256', 'unavailable')}")
    print("Graphify extraction performed: NO; promotion authorized: NO")
    for error in report.get("errors", []): print(f"FAIL: {error}")
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
