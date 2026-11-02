"""Evidence-aware knowledge contracts for the KMH OIA integrated pilot.

This module is deliberately deterministic and standard-library-only. It stores
candidate evidence separately from active evidence and only exposes records
that pass provenance and integrity validation.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import re
from typing import Iterable

from src.knowledge import KnowledgeItem


@dataclass(frozen=True)
class EvidenceRecord:
    evidence_id: str
    source_id: str
    source_uri: str
    locator: str
    content: str
    content_sha256: str
    captured_at: str
    status: str = "candidate"
    owner: str = "unassigned"

    @classmethod
    def create(
        cls,
        evidence_id: str,
        source_id: str,
        source_uri: str,
        locator: str,
        content: str,
        owner: str = "unassigned",
        captured_at: str | None = None,
    ) -> "EvidenceRecord":
        timestamp = captured_at or datetime.now(timezone.utc).isoformat()
        return cls(
            evidence_id=evidence_id,
            source_id=source_id,
            source_uri=source_uri,
            locator=locator,
            content=content,
            content_sha256=hashlib.sha256(content.encode("utf-8")).hexdigest(),
            captured_at=timestamp,
            owner=owner,
        )


@dataclass(frozen=True)
class Claim:
    claim_id: str
    text: str
    evidence_ids: tuple[str, ...]


@dataclass(frozen=True)
class VerificationResult:
    accepted: bool
    reason: str
    citations: tuple[str, ...] = ()


class EvidenceRegistry:
    """In-memory pilot registry; source evidence remains externally authoritative."""

    def __init__(self) -> None:
        self._records: dict[str, EvidenceRecord] = {}
        self._active_ids: set[str] = set()

    def add_candidate(self, record: EvidenceRecord) -> None:
        if not record.evidence_id.strip():
            raise ValueError("evidence_id must not be empty")
        if record.evidence_id in self._records:
            raise ValueError("evidence_id already exists")
        self._records[record.evidence_id] = record

    def get(self, evidence_id: str) -> EvidenceRecord | None:
        return self._records.get(evidence_id)

    def validate(self, evidence_id: str) -> VerificationResult:
        record = self.get(evidence_id)
        if record is None:
            return VerificationResult(False, "evidence_not_found")
        if not all((record.source_id, record.source_uri, record.locator, record.owner)):
            return VerificationResult(False, "provenance_incomplete")
        if not record.content.strip():
            return VerificationResult(False, "empty_evidence")
        actual = hashlib.sha256(record.content.encode("utf-8")).hexdigest()
        if actual != record.content_sha256:
            return VerificationResult(False, "content_hash_mismatch")
        return VerificationResult(True, "provenance_and_integrity_valid")

    def activate(self, evidence_id: str) -> VerificationResult:
        result = self.validate(evidence_id)
        if not result.accepted:
            return result
        self._active_ids.add(evidence_id)
        return VerificationResult(True, "activated", (self.citation(evidence_id),))

    def is_active(self, evidence_id: str) -> bool:
        return evidence_id in self._active_ids

    def citation(self, evidence_id: str) -> str:
        record = self._records[evidence_id]
        return f"{record.source_uri}#{record.locator} [evidence:{record.evidence_id}; sha256:{record.content_sha256}]"

    def active_records(self) -> tuple[EvidenceRecord, ...]:
        return tuple(self._records[key] for key in sorted(self._active_ids))


class ClaimVerifier:
    """Fail-closed verifier: every referenced record must be active and valid."""

    def __init__(self, registry: EvidenceRegistry, minimum_evidence: int = 1) -> None:
        if minimum_evidence < 1:
            raise ValueError("minimum_evidence must be at least one")
        self.registry = registry
        self.minimum_evidence = minimum_evidence

    def verify(self, claim: Claim) -> VerificationResult:
        if not claim.text.strip():
            return VerificationResult(False, "claim_empty")
        unique_ids = tuple(dict.fromkeys(claim.evidence_ids))
        if len(unique_ids) < self.minimum_evidence:
            return VerificationResult(False, "insufficient_evidence")
        citations: list[str] = []
        for evidence_id in unique_ids:
            if not self.registry.is_active(evidence_id):
                return VerificationResult(False, "evidence_not_active")
            result = self.registry.validate(evidence_id)
            if not result.accepted:
                return result
            citations.append(self.registry.citation(evidence_id))
        return VerificationResult(True, "verified", tuple(citations))


class EvidenceKnowledgeSource:
    """Adapter from active evidence into the existing OIA KnowledgeSource port."""

    def __init__(self, registry: EvidenceRegistry) -> None:
        self.registry = registry

    @staticmethod
    def _tokens(text: str) -> set[str]:
        return set(re.findall(r"[a-z0-9_]+", text.lower()))

    def retrieve(self, goal: str) -> list[KnowledgeItem]:
        query_tokens = self._tokens(goal)
        if not query_tokens:
            return []
        matches: list[KnowledgeItem] = []
        for record in self.registry.active_records():
            if not self.registry.validate(record.evidence_id).accepted:
                continue
            content_tokens = self._tokens(record.content)
            if query_tokens.intersection(content_tokens):
                citation = self.registry.citation(record.evidence_id)
                matches.append(KnowledgeItem(citation, record.content))
        return matches
