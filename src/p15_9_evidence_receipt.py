"""Stage 15 evidence receipt manifest.

This module records externally supplied evidence references without creating
or interpreting the underlying operational evidence. It provides deterministic
receipt-level traceability for one exact release.
"""

from dataclasses import dataclass
import re
from typing import Iterable


_SHA256 = re.compile(r"^[0-9a-fA-F]{64}$")


@dataclass(frozen=True)
class EvidenceReceipt:
    category: str
    release_id: str
    artifact_id: str
    observed_at: str
    source: str
    sha256: str

    def __post_init__(self) -> None:
        fields = {
            "category": self.category,
            "release_id": self.release_id,
            "artifact_id": self.artifact_id,
            "observed_at": self.observed_at,
            "source": self.source,
            "sha256": self.sha256,
        }
        for name, value in fields.items():
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} is required")
        if not _SHA256.fullmatch(self.sha256.strip()):
            raise ValueError("sha256 must be a 64-character hexadecimal digest")


@dataclass(frozen=True)
class EvidenceReceiptManifest:
    release_id: str
    receipts: tuple[EvidenceReceipt, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.release_id, str) or not self.release_id.strip():
            raise ValueError("release_id is required")
        if not self.receipts:
            raise ValueError("at least one evidence receipt is required")
        ids = [receipt.artifact_id for receipt in self.receipts]
        if len(ids) != len(set(ids)):
            raise ValueError("duplicate artifact_id is not allowed")


class EvidenceReceiptManifestBuilder:
    """Build receipt-level traceability from externally supplied records."""

    REQUIRED_CATEGORIES = (
        "telemetry",
        "performance",
        "rollback_drill",
        "authorization",
        "incident_exercise",
    )

    def build(
        self,
        *,
        release_id: str,
        receipts: Iterable[EvidenceReceipt],
    ) -> EvidenceReceiptManifest:
        release = release_id.strip() if isinstance(release_id, str) else ""
        if not release:
            raise ValueError("release_id is required")
        items = tuple(receipts)
        if not items:
            raise ValueError("at least one evidence receipt is required")
        for receipt in items:
            if not isinstance(receipt, EvidenceReceipt):
                raise ValueError("receipts must contain EvidenceReceipt values")
            if receipt.release_id != release:
                raise ValueError("receipt release_id does not match manifest release_id")
        return EvidenceReceiptManifest(release, items)

    def missing_categories(self, manifest: EvidenceReceiptManifest) -> tuple[str, ...]:
        if not isinstance(manifest, EvidenceReceiptManifest):
            raise ValueError("evidence receipt manifest is required")
        present = {receipt.category for receipt in manifest.receipts}
        return tuple(category for category in self.REQUIRED_CATEGORIES if category not in present)
