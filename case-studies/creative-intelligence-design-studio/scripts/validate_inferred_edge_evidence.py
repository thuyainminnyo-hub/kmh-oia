#!/usr/bin/env python3
"""Verify source facts for the held Graphify INFERRED edge; never promotes it."""
from __future__ import annotations
import argparse
import ast
import json
from pathlib import Path
from typing import Any


def inspect_held_edge(scan_root: Path) -> dict[str, Any]:
    root = Path(scan_root).resolve()
    flow_path = root / "src/outfit_flow.py"
    guard_path = root / "src/contract_guard.py"
    errors: list[str] = []
    evidence: dict[str, Any] = {}
    for path in (flow_path, guard_path):
        if not path.is_file() or path.is_symlink():
            errors.append(f"approved source file missing or unsafe: {path.name}")
    if errors:
        return {"status": "FAIL", "errors": errors, "evidence": evidence}
    try:
        flow = ast.parse(flow_path.read_text(encoding="utf-8"), filename=str(flow_path))
        guard = ast.parse(guard_path.read_text(encoding="utf-8"), filename=str(guard_path))
    except (OSError, UnicodeError, SyntaxError) as exc:
        return {"status": "FAIL", "errors": [f"source parse failed: {exc}"], "evidence": evidence}

    imports = [n for n in ast.walk(flow) if isinstance(n, ast.ImportFrom) and n.module == "contract_guard"]
    imported = {a.asname or a.name for n in imports for a in n.names}
    if not imports or "DesignToken" not in imported:
        errors.append("outfit_flow.py does not import DesignToken from contract_guard")
    else:
        evidence["cross_file_import"] = {"file": "src/outfit_flow.py", "line": imports[0].lineno, "module": "contract_guard", "names": sorted(imported)}

    fn = next((n for n in ast.walk(flow) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == "select_outfit"), None)
    if fn is None:
        errors.append("select_outfit function is missing")
    else:
        args = [*fn.args.posonlyargs, *fn.args.args, *fn.args.kwonlyargs]
        token_arg = next((a for a in args if a.arg == "token"), None)
        type_ok = token_arg is not None and isinstance(token_arg.annotation, ast.Name) and token_arg.annotation.id == "DesignToken"
        if not type_ok:
            errors.append("select_outfit token parameter is not explicitly annotated as DesignToken")
        else:
            evidence["type_annotation"] = {
                "file": "src/outfit_flow.py", "line": token_arg.annotation.lineno,
                "function": "select_outfit", "parameter": "token", "type": "DesignToken",
                "matches_graph_edge_source_location": token_arg.annotation.lineno == 6
            }
        field_uses = [
            {"field": n.attr, "line": n.lineno}
            for n in ast.walk(fn)
            if isinstance(n, ast.Attribute) and isinstance(n.value, ast.Name)
            and n.value.id == "token" and n.attr in {"token_name", "approved"}
        ]
        if not field_uses:
            errors.append("select_outfit does not access fields on its typed token parameter")
        else:
            evidence["runtime_parameter_field_access"] = field_uses
        calls = [
            {"line": n.lineno, "arguments": [a.id for a in n.args if isinstance(a, ast.Name)]}
            for n in ast.walk(fn)
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "is_approved_token"
        ]
        if not any("token" in c["arguments"] for c in calls):
            errors.append("select_outfit does not pass token to is_approved_token")
        else:
            evidence["approval_check"] = calls

    target = next((n for n in ast.walk(guard) if isinstance(n, ast.ClassDef) and n.name == "DesignToken"), None)
    if target is None:
        errors.append("contract_guard.py does not define DesignToken")
    else:
        fields = sorted({n.target.id for n in ast.walk(target) if isinstance(n, ast.AnnAssign) and isinstance(n.target, ast.Name)})
        if not {"token_name", "approved"}.issubset(fields):
            errors.append("DesignToken is missing expected token_name / approved fields")
        evidence["target_definition"] = {"file": "src/contract_guard.py", "line": target.lineno, "class": "DesignToken", "fields": fields}

    return {
        "status": "PASS" if not errors else "FAIL",
        "errors": errors,
        "evidence": evidence,
        "decision": {
            "owner_disposition": "CONFIRMED_HOLD",
            "edge_confidence": "INFERRED",
            "promotion": "NOT_AUTHORIZED",
            "additional_semantic_review": "REQUIRED",
            "raw_graph_mutated": False,
            "candidate_graph_mutated": False
        }
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scan-root", required=True, type=Path)
    parser.add_argument("--report-out", required=True, type=Path)
    args = parser.parse_args()
    report = inspect_held_edge(args.scan_root)
    args.report_out.parent.mkdir(parents=True, exist_ok=True)
    args.report_out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"Held-edge source corroboration: {report['status']}")
    print("Owner HOLD: CONFIRMED; promotion: NOT AUTHORIZED")
    for error in report["errors"]:
        print(f"FAIL: {error}")
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
