"""Fail-closed publication readiness checks for the KMH Laphet pilot.

This module validates a single heritage record before publication. It does not
collect data, grant consent, assess food safety, or publish content.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any, Mapping

_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_ALLOWED_RECORD_ACCESS = {
    "PUBLIC", "COMMUNITY", "RESEARCH", "RESTRICTED", "SACRED_SENSITIVE", "WITHDRAWN"
}
_ALLOWED_CLAIM_STATES = {"SUPPORTED", "CORROBORATED", "COMMUNITY_CONFIRMED"}
_PRIVATE_EVIDENCE_TYPES = {
    "community_interview", "oral_history", "photograph", "audio", "video",
    "recipe_record", "producer_record", "consent_record", "community_authority_record",
    "community_review_record", "cultural_review_record", "scientific_review_record",
    "expert_review_record", "qa_report", "approval_record", "community_approval"
}
_SCIENTIFIC_CLAIMS = {"MICROBIOLOGY", "NUTRITION", "FOOD_SAFETY"}
_REVIEW_EVIDENCE_TYPES = {
    "cultural": {"community_review_record", "cultural_review_record"},
    "scientific": {"scientific_review_record", "expert_review_record"},
    "independent_qa": {"qa_report"},
    "community_publication": {"approval_record", "community_approval"},
}


def assess_publication_readiness(record: Mapping[str, Any]) -> dict[str, Any]:
    """Return a deterministic, fail-closed publication gate assessment."""
    errors: list[str] = []

    if not isinstance(record, Mapping):
        return {"eligible": False, "errors": ["record must be a JSON object"]}

    if record.get("record_status") != "APPROVED_FOR_PUBLICATION":
        errors.append("record_status must be APPROVED_FOR_PUBLICATION")

    record_access = record.get("access_classification")
    if record_access != "PUBLIC" or record_access not in _ALLOWED_RECORD_ACCESS:
        errors.append("record access_classification must be PUBLIC")

    evidence_rows = record.get("evidence", [])
    if not isinstance(evidence_rows, list):
        evidence_rows = []
        errors.append("evidence must be an array")

    evidence_by_id: dict[str, Mapping[str, Any]] = {}
    for index, item in enumerate(evidence_rows):
        if not isinstance(item, Mapping):
            errors.append(f"evidence[{index}] must be an object")
            continue
        evidence_id = item.get("id")
        if not isinstance(evidence_id, str) or not evidence_id.strip():
            errors.append(f"evidence[{index}].id is required")
            continue
        if evidence_id in evidence_by_id:
            errors.append(f"duplicate evidence id: {evidence_id}")
        evidence_by_id[evidence_id] = item
        evidence_access = item.get("access_classification")
        if not isinstance(evidence_access, str) or evidence_access not in _ALLOWED_RECORD_ACCESS:
            errors.append(f"evidence {evidence_id} has an invalid access_classification")

    def require_existing_refs(refs: Any, label: str) -> list[str]:
        if not isinstance(refs, list) or not refs:
            errors.append(f"{label} must contain at least one evidence id")
            return []
        normalized: list[str] = []
        for reference in refs:
            if not isinstance(reference, str) or reference not in evidence_by_id:
                errors.append(f"{label} references missing evidence: {reference!r}")
            else:
                normalized.append(reference)
        return normalized

    community = record.get("community")
    if not isinstance(community, Mapping):
        community = {}
        errors.append("community object is required")
    if not isinstance(community.get("community_reference"), str) or not community.get("community_reference", "").strip():
        errors.append("community.community_reference is required")
    if community.get("authority_status") != "VERIFIED":
        errors.append("community.authority_status must be VERIFIED")
    authority_refs = require_existing_refs(
        community.get("authority_evidence_ids"), "community.authority_evidence_ids"
    )
    for evidence_id in authority_refs:
        if evidence_by_id[evidence_id].get("evidence_type") != "community_authority_record":
            errors.append(f"community authority evidence has the wrong type: {evidence_id}")

    consent = record.get("consent")
    if not isinstance(consent, Mapping):
        consent = {}
        errors.append("consent object is required")
    if consent.get("status") != "ACTIVE":
        errors.append("consent.status must be ACTIVE")

    scopes = consent.get("scopes")
    if not isinstance(scopes, Mapping):
        scopes = {}
        errors.append("consent.scopes object is required")
    for scope in ("documentation", "public_publication"):
        if scopes.get(scope) is not True:
            errors.append(f"consent scope {scope} must be explicitly true")

    attribution_mode = record.get("attribution_mode")
    if attribution_mode == "NAMED" and scopes.get("attribution") is not True:
        errors.append("named attribution requires explicit attribution consent")
    if not isinstance(attribution_mode, str) or attribution_mode not in {"NAMED", "COMMUNITY_ONLY", "ANONYMOUS"}:
        errors.append("attribution_mode must be NAMED, COMMUNITY_ONLY, or ANONYMOUS")

    consent_refs = require_existing_refs(consent.get("evidence_ids"), "consent.evidence_ids")
    for evidence_id in consent_refs:
        if evidence_by_id[evidence_id].get("evidence_type") != "consent_record":
            errors.append(f"consent evidence has the wrong type: {evidence_id}")

    reviews = record.get("reviews")
    if not isinstance(reviews, Mapping):
        reviews = {}
        errors.append("reviews object is required")

    required_reviews = ("cultural", "scientific", "independent_qa", "community_publication")
    for review_name in required_reviews:
        review = reviews.get(review_name)
        if not isinstance(review, Mapping):
            errors.append(f"reviews.{review_name} object is required")
            continue
        if review.get("status") != "PASS":
            errors.append(f"reviews.{review_name}.status must be PASS")
        reviewer_ref = review.get("reviewer_ref")
        if not isinstance(reviewer_ref, str) or not reviewer_ref.strip():
            errors.append(f"reviews.{review_name}.reviewer_ref is required")
        review_refs = require_existing_refs(
            review.get("evidence_ids"), f"reviews.{review_name}.evidence_ids"
        )
        expected_types = _REVIEW_EVIDENCE_TYPES[review_name]
        for evidence_id in review_refs:
            evidence_type = evidence_by_id[evidence_id].get("evidence_type")
            if not isinstance(evidence_type, str) or evidence_type not in expected_types:
                errors.append(f"reviews.{review_name} evidence has the wrong type: {evidence_id}")

    publication_review = reviews.get("community_publication")
    publication = record.get("publication")
    if not isinstance(publication, Mapping):
        publication = {}
        errors.append("publication object is required")
    if publication.get("status") != "APPROVED":
        errors.append("publication.status must be APPROVED")

    artifact_sha = publication.get("artifact_sha256")
    if not isinstance(artifact_sha, str) or not _SHA256.fullmatch(artifact_sha):
        errors.append("publication.artifact_sha256 must be a lowercase SHA-256 digest")
    if isinstance(publication_review, Mapping):
        if publication_review.get("artifact_sha256") != artifact_sha:
            errors.append("community publication review must approve the exact publication artifact hash")

    channels = publication.get("channels")
    if not isinstance(channels, list) or not channels or any(not isinstance(v, str) or not v.strip() for v in channels):
        errors.append("publication.channels must contain at least one non-empty value")
    else:
        allowed_channels = consent.get("allowed_channels")
        if (
            not isinstance(allowed_channels, list)
            or any(not isinstance(value, str) or not value.strip() for value in allowed_channels)
            or not set(channels).issubset(set(allowed_channels))
        ):
            errors.append("publication.channels must be within the channels explicitly allowed by consent")

    languages = publication.get("languages")
    if not isinstance(languages, list) or not languages or any(not isinstance(v, str) or not v.strip() for v in languages):
        errors.append("publication.languages must contain at least one non-empty value")
    else:
        allowed_languages = consent.get("allowed_languages")
        if (
            not isinstance(allowed_languages, list)
            or any(not isinstance(value, str) or not value.strip() for value in allowed_languages)
            or not set(languages).issubset(set(allowed_languages))
        ):
            errors.append("publication.languages must be within the languages explicitly allowed by consent")
        if len(set(languages)) > 1 and scopes.get("translation") is not True:
            errors.append("multilingual publication requires explicit translation consent")

    publication_refs = require_existing_refs(
        publication.get("approval_evidence_ids"), "publication.approval_evidence_ids"
    )
    for evidence_id in publication_refs:
        evidence_type = evidence_by_id[evidence_id].get("evidence_type")
        if not isinstance(evidence_type, str) or evidence_type not in {"approval_record", "community_approval"}:
            errors.append(f"publication approval reference is not an approval record: {evidence_id}")

    claims = record.get("claims")
    if not isinstance(claims, list) or not claims:
        claims = []
        errors.append("at least one claim is required for a heritage publication")

    food_safety_claim_present = False
    for index, claim in enumerate(claims):
        label = f"claims[{index}]"
        if not isinstance(claim, Mapping):
            errors.append(f"{label} must be an object")
            continue
        if claim.get("public") is not True:
            continue
        if claim.get("status") not in _ALLOWED_CLAIM_STATES:
            errors.append(f"{label}.status must be a supported, corroborated, or community-confirmed state")
        if not isinstance(claim.get("text"), str) or not claim.get("text", "").strip():
            errors.append(f"{label}.text is required")
        category = claim.get("category")
        if not isinstance(category, str):
            errors.append(f"{label}.category must be a string")
            continue
        if category == "HEALTH":
            errors.append(f"{label}: health/medical claims are outside this pilot's publication scope")
        refs = require_existing_refs(claim.get("evidence_ids"), f"{label}.evidence_ids")
        for evidence_id in refs:
            evidence = evidence_by_id[evidence_id]
            if evidence.get("access_classification") != "PUBLIC":
                errors.append(f"{label} uses non-public evidence {evidence_id}")
            evidence_type = evidence.get("evidence_type")
            if isinstance(evidence_type, str) and evidence_type in _PRIVATE_EVIDENCE_TYPES:
                errors.append(f"{label}: internal or contributor evidence cannot be used as public claim evidence: {evidence_id}")
            if evidence.get("publication_permission") is not True:
                errors.append(f"{label} uses evidence without publication permission: {evidence_id}")
            if evidence.get("evidence_type") in _PRIVATE_EVIDENCE_TYPES:
                permission_ref = evidence.get("permission_evidence_id")
                if permission_ref not in consent_refs:
                    errors.append(f"{label} uses contributor/media evidence without matching consent evidence: {evidence_id}")
        science_review = reviews.get("scientific")
        if category in _SCIENTIFIC_CLAIMS and (
            not isinstance(science_review, Mapping) or science_review.get("status") != "PASS"
        ):
            errors.append(f"{label}: scientific claims require a PASS scientific review")
        if category == "FOOD_SAFETY":
            food_safety_claim_present = True
            safety = record.get("food_safety")
            if not isinstance(safety, Mapping) or safety.get("status") != "PASS":
                errors.append(f"{label}: food-safety claims require a PASS batch-specific safety assessment")
            lab_evidence = [
                evidence_by_id[evidence_id]
                for evidence_id in refs
                if evidence_by_id[evidence_id].get("evidence_type") == "lab_report"
            ]
            if not lab_evidence:
                errors.append(f"{label}: food-safety claims require a referenced laboratory report")
            for report in lab_evidence:
                for field in ("laboratory_reference", "test_method", "sample_id", "chain_of_custody_ref"):
                    if not isinstance(report.get(field), str) or not report.get(field, "").strip():
                        errors.append(f"{label}: laboratory report requires {field}")
            safety = record.get("food_safety")
            if not isinstance(safety, Mapping) or safety.get("status") != "PASS":
                errors.append(f"{label}: food-safety claims require a PASS batch-specific safety assessment")
            elif isinstance(safety, Mapping):
                safety_refs = require_existing_refs(safety.get("evidence_ids"), "food_safety.evidence_ids")
                for safety_ref in safety_refs:
                    if evidence_by_id[safety_ref].get("evidence_type") != "lab_report":
                        errors.append(f"food_safety evidence must be a laboratory report: {safety_ref}")
                if not set(evidence_id for evidence_id in refs if evidence_by_id[evidence_id].get("evidence_type") == "lab_report").issubset(set(safety_refs)):
                    errors.append(f"{label}: claim laboratory evidence must also be included in food_safety.evidence_ids")

    if food_safety_claim_present and not isinstance(record.get("food_safety"), Mapping):
        errors.append("food_safety object is required for a food-safety claim")

    return {"eligible": not errors, "errors": errors}


def main() -> int:
    parser = argparse.ArgumentParser(description="Check the KMH Laphet pilot publication gate.")
    parser.add_argument("record", type=Path, help="Path to a Laphet pilot record JSON file")
    args = parser.parse_args()
    try:
        record = json.loads(args.record.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(json.dumps({"eligible": False, "errors": [str(exc)]}, ensure_ascii=False, indent=2))
        return 2
    result = assess_publication_readiness(record)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["eligible"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
