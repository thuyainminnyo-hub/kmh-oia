"""Evidence-linked, conservative site analysis for the landscape design pilot.

This module summarizes validated observations and reports evidence gaps. It does
not infer missing measurements or produce construction-ready design advice.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal, Mapping, Sequence

from src.landscape_registry import (
    ObservationCategory,
    QAStatus,
    ValidationIssue,
    validate_observation_payload,
    validate_site_payload,
)


REQUIRED_ANALYSIS_CATEGORIES = (
    ObservationCategory.TOPOGRAPHY,
    ObservationCategory.SUN,
    ObservationCategory.DRAINAGE,
    ObservationCategory.CLIMATE,
    ObservationCategory.VEGETATION,
    ObservationCategory.ACCESS,
    ObservationCategory.UTILITIES,
    ObservationCategory.HAZARD,
)


@dataclass(frozen=True)
class AnalysisFinding:
    code: str
    severity: Literal["info", "warning", "hold"]
    message: str
    evidence_refs: tuple[str, ...] = ()


@dataclass(frozen=True)
class CategorySummary:
    category: ObservationCategory
    observation_ids: tuple[str, ...]
    evidence_refs: tuple[str, ...]
    limitations: tuple[str, ...]


@dataclass(frozen=True)
class SiteAnalysisReport:
    site_id: str | None
    status: QAStatus
    observed_categories: tuple[ObservationCategory, ...]
    missing_categories: tuple[ObservationCategory, ...]
    category_summaries: tuple[CategorySummary, ...]
    findings: tuple[AnalysisFinding, ...]
    validation_issues: tuple[ValidationIssue, ...]

    @property
    def is_complete(self) -> bool:
        return not self.missing_categories and not self.validation_issues


def analyze_site(
    site_payload: Mapping[str, Any],
    observation_payloads: Sequence[Mapping[str, Any]],
) -> SiteAnalysisReport:
    """Validate supplied records, summarize evidence coverage, and fail closed.

    Missing categories are reported as gaps, never synthesized. Any validation
    issue, cross-site reference mismatch, or missing required category keeps the
    analysis status at HOLD.
    """
    findings: list[AnalysisFinding] = []
    issues: list[ValidationIssue] = []

    if not isinstance(site_payload, Mapping):
        issue = ValidationIssue(
            "invalid_site_payload", "site",
            "Site payload must be a mapping.", "error",
        )
        return SiteAnalysisReport(
            None, QAStatus.HOLD, (), REQUIRED_ANALYSIS_CATEGORIES, (),
            (AnalysisFinding("analysis_input_invalid", "hold", issue.message),),
            (issue,),
        )

    site_report = validate_site_payload(site_payload)
    issues.extend(site_report.issues)
    site_id = site_payload.get("site_id")
    if not site_report.is_valid:
        findings.append(AnalysisFinding(
            "site_registry_invalid", "hold",
            "Site registry validation failed; analysis is held until required fields and provenance are corrected.",
            tuple(str(ref) for ref in site_payload.get("source_refs", ()) if isinstance(ref, str)),
        ))

    if not isinstance(observation_payloads, Sequence) or isinstance(observation_payloads, (str, bytes)):
        issue = ValidationIssue(
            "invalid_observations_payload", "observations",
            "Observations must be a sequence of observation mappings.", "error",
        )
        issues.append(issue)
        findings.append(AnalysisFinding("analysis_input_invalid", "hold", issue.message))
        observation_payloads = ()

    grouped: dict[ObservationCategory, list[Mapping[str, Any]]] = {
        category: [] for category in ObservationCategory
    }
    for index, payload in enumerate(observation_payloads):
        if not isinstance(payload, Mapping):
            issues.append(ValidationIssue(
                "invalid_observation_payload", f"observations[{index}]",
                "Each observation must be a mapping.", "error",
            ))
            findings.append(AnalysisFinding(
                "observation_input_invalid", "hold",
                f"Observation at index {index} is not a mapping.",
            ))
            continue

        report = validate_observation_payload(payload)
        issues.extend(
            ValidationIssue(
                issue.code, f"observations[{index}].{issue.path}",
                issue.message, issue.severity,
            )
            for issue in report.issues
        )
        if not report.is_valid:
            findings.append(AnalysisFinding(
                "observation_registry_invalid", "hold",
                f"Observation at index {index} failed registry validation.",
                (payload.get("source_ref"),) if isinstance(payload.get("source_ref"), str) and payload.get("source_ref").strip() else (),
            ))
            continue

        observation_site_id = payload.get("site_id")
        if observation_site_id != site_id:
            issues.append(ValidationIssue(
                "observation_site_mismatch", f"observations[{index}].site_id",
                "Observation site_id must match the analyzed site.", "error",
            ))
            findings.append(AnalysisFinding(
                "observation_site_mismatch", "hold",
                f"Observation {payload.get('observation_id', index)!r} belongs to a different site.",
                (payload["source_ref"],),
            ))
            continue

        try:
            category = ObservationCategory(payload["category"])
        except (ValueError, TypeError):
            # The registry validator has already emitted the category issue.
            continue
        grouped[category].append(payload)

    summaries: list[CategorySummary] = []
    observed: list[ObservationCategory] = []
    missing: list[ObservationCategory] = []

    for category in REQUIRED_ANALYSIS_CATEGORIES:
        records = grouped[category]
        if not records:
            missing.append(category)
            findings.append(AnalysisFinding(
                "required_evidence_missing", "hold",
                f"No validated {category.value} observation is available; this category remains unknown.",
            ))
            continue

        observed.append(category)
        summaries.append(CategorySummary(
            category=category,
            observation_ids=tuple(str(record["observation_id"]) for record in records),
            evidence_refs=tuple(str(record["source_ref"]) for record in records),
            limitations=tuple(
                str(record.get("limitations", "")).strip()
                for record in records
                if isinstance(record.get("limitations", ""), str) and record.get("limitations", "").strip()
            ),
        ))
        low_confidence = [
            record for record in records
            if isinstance(record.get("confidence"), (int, float))
            and not isinstance(record.get("confidence"), bool)
            and record["confidence"] < 0.6
        ]
        if low_confidence:
            findings.append(AnalysisFinding(
                "low_confidence_evidence", "warning",
                f"{category.value} includes observation(s) with confidence below 0.6; review source quality before design decisions.",
                tuple(str(record["source_ref"]) for record in low_confidence),
            ))

    status = QAStatus.HOLD if issues or missing else QAStatus.PASS
    if status is QAStatus.PASS:
        findings.append(AnalysisFinding(
            "evidence_coverage_complete", "info",
            "All required analysis categories have validated, site-matched evidence. This is a coverage check, not design approval.",
            tuple(ref for summary in summaries for ref in summary.evidence_refs),
        ))
    else:
        findings.append(AnalysisFinding(
            "analysis_not_approved", "hold",
            "Site analysis is not approved for downstream design decisions while validation errors or required evidence gaps remain.",
        ))

    return SiteAnalysisReport(
        site_id=site_id if isinstance(site_id, str) else None,
        status=status,
        observed_categories=tuple(observed),
        missing_categories=tuple(missing),
        category_summaries=tuple(summaries),
        findings=tuple(findings),
        validation_issues=tuple(issues),
    )
