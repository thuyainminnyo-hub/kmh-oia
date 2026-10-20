"""Independent structural QA for persisted runtime evidence artifacts.

This gate verifies artifact integrity and explicit acceptance criteria only. A PASS
is not an independent business-quality judgment, outcome proof, or release approval.
It never mutates or promotes the source EvidenceObject.
"""
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any
import uuid

from src.evidence_object import EvidenceObject


@dataclass(frozen=True)
class QACheck:
    name: str
    passed: bool
    detail: str


@dataclass(frozen=True)
class QAVerdict:
    qa_id: str
    evidence_id: str
    status: str
    checked_at: str
    artifact_digest: str | None
    checks: tuple[QACheck, ...]
    reason: str

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["checks"] = [asdict(check) for check in self.checks]
        return data


def evaluate_evidence(
    evidence: EvidenceObject,
    expected_output: str | None = None,
) -> QAVerdict:
    """Check artifact bytes, JSON structure, provenance linkage, and optional output.

    Missing/unreadable or malformed artifacts return NOT_VERIFIED. Integrity,
    identity, or acceptance-criterion mismatches return FAIL. PASS means all
    performed checks passed; it does not promote EvidenceObject.validation_state.
    """
    if not isinstance(evidence, EvidenceObject):
        raise TypeError("evidence must be an EvidenceObject")

    checked_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    checks: list[QACheck] = []
    artifact_digest: str | None = None
    status = "NOT_VERIFIED"
    reason = "artifact could not be independently inspected"

    if not evidence.artifact_ref:
        checks.append(QACheck("artifact_ref_present", False, "Evidence has no artifact_ref"))
    else:
        path = Path(evidence.artifact_ref)
        try:
            raw = path.read_bytes()
        except OSError as exc:
            checks.append(QACheck("artifact_readable", False, type(exc).__name__))
        else:
            artifact_digest = hashlib.sha256(raw).hexdigest()
            digest_match = (
                evidence.sha256_digest is not None
                and artifact_digest == evidence.sha256_digest
            )
            checks.append(QACheck(
                "sha256_matches_evidence",
                digest_match,
                "persisted bytes match recorded digest" if digest_match else "digest missing or mismatched",
            ))
            try:
                payload = json.loads(raw.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                checks.append(QACheck("valid_json_artifact", False, type(exc).__name__))
                payload = None
            else:
                is_object = isinstance(payload, dict)
                checks.append(QACheck(
                    "json_object",
                    is_object,
                    "top-level JSON object" if is_object else "top-level JSON value must be an object",
                ))
                if is_object:
                    for name, expected in (("run_id", evidence.run_id), ("trace_id", evidence.trace_id)):
                        if expected is not None:
                            actual = payload.get(name)
                            checks.append(QACheck(
                                f"{name}_matches_evidence",
                                actual == expected,
                                "matches evidence provenance" if actual == expected else f"artifact {name} does not match evidence",
                            ))
                    required = ("output", "stages", "events")
                    for name in required:
                        ok = name in payload
                        checks.append(QACheck(
                            f"{name}_present",
                            ok,
                            "present" if ok else f"artifact is missing {name}",
                        ))
                    if expected_output is not None:
                        ok = payload.get("output") == expected_output
                        checks.append(QACheck(
                            "expected_output_matches",
                            ok,
                            "output matches supplied acceptance criterion" if ok else "output differs from expected_output",
                        ))

            if not any(not c.passed for c in checks):
                status = "PASS"
                reason = "artifact integrity, provenance linkage, and requested structural criteria passed"
            elif any(c.name == "sha256_matches_evidence" and not c.passed for c in checks):
                status = "FAIL"
                reason = "artifact digest integrity check failed"
            else:
                status = "FAIL"
                reason = "one or more structural or acceptance checks failed"

    return QAVerdict(
        qa_id=f"qa:{uuid.uuid4()}",
        evidence_id=evidence.evidence_id,
        status=status,
        checked_at=checked_at,
        artifact_digest=artifact_digest,
        checks=tuple(checks),
        reason=reason,
    )


def write_verdict(verdict: QAVerdict, path: str | Path) -> None:
    """Append a standalone QA verdict JSON line; never updates evidence records."""
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(verdict.to_dict(), sort_keys=True, ensure_ascii=False) + "\n")
        stream.flush()
