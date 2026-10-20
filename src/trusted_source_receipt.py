"""Trusted external source receipt verification primitives.

This module defines the adapter boundary only. Production adapters must verify
receipts using the provider's real API/signature mechanism; caller booleans are
not trusted. Freshness is checked here, while persistent replay prevention must
be enforced by a durable store supplied by the runtime deployment.
"""
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Protocol

from src.receipt_replay_store import InMemoryReceiptReplayStore, ReceiptReplayStore


@dataclass(frozen=True)
class TrustedSourceReceipt:
    provider_name: str
    source_record_id: str
    execution_id: str
    raw_observation: str
    observed_at: str
    content_hash: str
    verification_method: str


@dataclass(frozen=True)
class ReceiptVerificationResult:
    verified: bool
    provider_name: str
    source_record_id: str
    execution_id: str
    raw_observation: str
    verification_method: str
    reasons: tuple[str, ...]


class TrustedSourceAdapter(Protocol):
    """Provider-specific receipt adapter; never implement with caller assertions."""

    @property
    def provider_name(self) -> str: ...

    def fetch_receipt(
        self, source_record_id: str, execution_id: str
    ) -> TrustedSourceReceipt | None: ...

    def verify_receipt(self, receipt: TrustedSourceReceipt) -> bool: ...

    def match_execution(
        self, receipt: TrustedSourceReceipt, execution_id: str
    ) -> bool: ...


class TrustedSourceReceiptVerifier:
    """Validate allowlist, receipt integrity, attribution, and receipt freshness."""

    def __init__(
        self,
        adapter: TrustedSourceAdapter | None,
        *,
        allowed_providers: tuple[str, ...] = (),
        max_receipt_age_seconds: int = 86400,
        clock=None,
        replay_store: ReceiptReplayStore | None = None,
    ) -> None:
        if max_receipt_age_seconds < 0:
            raise ValueError("max_receipt_age_seconds must be non-negative")
        self.adapter = adapter
        self.allowed_providers = frozenset(
            provider.strip() for provider in allowed_providers if provider.strip()
        )
        self.max_receipt_age_seconds = max_receipt_age_seconds
        self.clock = clock or (lambda: datetime.now(timezone.utc))
        self.replay_store = replay_store or InMemoryReceiptReplayStore()

    def verify(
        self, source_record_id: str, execution_id: str
    ) -> ReceiptVerificationResult:
        adapter = self.adapter
        provider = adapter.provider_name.strip() if adapter is not None else ""
        record_id = source_record_id.strip() if isinstance(source_record_id, str) else ""
        execution = execution_id.strip() if isinstance(execution_id, str) else ""

        if adapter is None:
            return self._rejected("", record_id, execution, "No trusted source adapter is configured.")
        if not provider:
            return self._rejected("", record_id, execution, "Adapter provider name is required.")
        if not self.allowed_providers or provider not in self.allowed_providers:
            return self._rejected(provider, record_id, execution, "Provider is not allowlisted.")
        if not record_id or not execution:
            return self._rejected(provider, record_id, execution, "Source record ID and execution ID are required.")

        try:
            receipt = adapter.fetch_receipt(record_id, execution)
            if receipt is None:
                return self._rejected(provider, record_id, execution, "Provider did not return a receipt.")
            if receipt.provider_name != provider:
                return self._rejected(provider, record_id, execution, "Receipt provider does not match the configured adapter.")
            if receipt.source_record_id != record_id:
                return self._rejected(provider, record_id, execution, "Receipt record ID does not match the requested record.")
            if receipt.execution_id != execution:
                return self._rejected(provider, record_id, execution, "Receipt is not linked to this execution ID.")
            if not receipt.raw_observation.strip():
                return self._rejected(provider, record_id, execution, "Receipt raw observation is missing.")
            if not receipt.content_hash.strip():
                return self._rejected(provider, record_id, execution, "Receipt content hash is missing.")
            if not receipt.verification_method.strip():
                return self._rejected(provider, record_id, execution, "Receipt verification method is missing.")
            freshness_reason = self._check_freshness(receipt.observed_at)
            if freshness_reason:
                return self._rejected(provider, record_id, execution, freshness_reason)
            if not adapter.verify_receipt(receipt):
                return self._rejected(provider, record_id, execution, "Provider receipt integrity/authenticity verification failed.")
            if not adapter.match_execution(receipt, execution):
                return self._rejected(provider, record_id, execution, "Provider attribution check did not match the execution.")
        except Exception as exc:
            # Avoid returning arbitrary provider exception data that may contain secrets.
            return self._rejected(provider, record_id, execution, f"Receipt verification failed safely ({type(exc).__name__}).")

        replay_claim = self.replay_store.claim(
            provider,
            record_id,
            receipt.content_hash,
        )
        if not replay_claim.accepted:
            return self._rejected(provider, record_id, execution, replay_claim.reason)

        return ReceiptVerificationResult(
            verified=True,
            provider_name=provider,
            source_record_id=record_id,
            execution_id=execution,
            raw_observation=receipt.raw_observation,
            verification_method=receipt.verification_method,
            reasons=("Trusted provider receipt integrity, freshness, attribution, and replay checks passed.",),
        )

    def _check_freshness(self, observed_at: str) -> str | None:
        if not isinstance(observed_at, str) or not observed_at.strip():
            return "Receipt timestamp is missing."
        try:
            timestamp_text = observed_at.strip()
            if timestamp_text.endswith("Z"):
                timestamp_text = timestamp_text[:-1] + "+00:00"
            observed = datetime.fromisoformat(timestamp_text)
            if observed.tzinfo is None:
                return "Receipt timestamp must include a timezone."
            now = self.clock()
            if now.tzinfo is None:
                return "Verifier clock must include a timezone."
            age = (now.astimezone(timezone.utc) - observed.astimezone(timezone.utc)).total_seconds()
        except (TypeError, ValueError, OverflowError):
            return "Receipt timestamp is invalid."
        if age < 0:
            return "Receipt timestamp is in the future."
        if age > self.max_receipt_age_seconds:
            return "Receipt is stale and exceeds the maximum allowed age."
        return None

    @staticmethod
    def _rejected(
        provider: str, record_id: str, execution: str, reason: str
    ) -> ReceiptVerificationResult:
        return ReceiptVerificationResult(
            verified=False,
            provider_name=provider,
            source_record_id=record_id,
            execution_id=execution,
            raw_observation="",
            verification_method="",
            reasons=(reason,),
        )
