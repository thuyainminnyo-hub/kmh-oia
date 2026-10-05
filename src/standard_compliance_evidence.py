"""Turn runtime standard checks into traceable QA evidence."""
from dataclasses import dataclass
from .standard_runtime_bridge import RuntimeStandardCheck

@dataclass(frozen=True)
class StandardComplianceEvidence:
    command_id: str
    standard_id: str
    compliant: bool
    rule: str
    qa_status: str
    evidence_type: str = "standard_compliance"

class StandardComplianceEvidenceBuilder:
    def build(self, check: RuntimeStandardCheck, *, rule: str, qa_status: str = "PASS") -> StandardComplianceEvidence:
        if not check.allowed or not check.compliance.compliant:
            raise ValueError("only compliant runtime checks can become compliance evidence")
        if qa_status not in {"PASS", "FAIL"}:
            raise ValueError("qa_status must be PASS or FAIL")
        return StandardComplianceEvidence(check.command_id, check.standard_id, True, rule, qa_status)
