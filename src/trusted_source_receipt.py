"""Trusted external source receipt verification primitives.

This module defines the adapter boundary only. A production provider adapter must
implement authentic receipt verification and execution attribution using the
provider's actual API/signature mechanism; caller booleans are not trusted.
"""
from dataclasses import dataclass
from typing import Protocol


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
    """Validate receipt provenance and attribution using an injected adapter."""

    def __init__(
        self,
        adapter: TrustedSourceAdapter | None,
        *,
        allowed_providers: tuple[str, ...] = (),
    ) -> None:
        self.adapter = adapter
        self.allowed_providers = frozenset(
            provider.strip() for provider in allowed_providers if provider.strip()
        )

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
            if not receipt.observed_at.strip() or not receipt.content_hash.strip():
                return self._rejected(provider, record_id, execution, "Receipt timestamp or content hash is missing.")
            if not receipt.verification_method.strip():
                return self._rejected(provider, record_id, execution, "Receipt verification method is missing.")
            if not adapter.verify_receipt(receipt):
                return self._rejected(provider, record_id, execution, "Provider receipt integrity/authenticity verification failed.")
            if not adapter.match_execution(receipt, execution):
                return self._rejected(provider, record_id, execution, "Provider attribution check did not match the execution.")
        except Exception as exc:
            # Avoid returning arbitrary provider exception data that may contain secrets.
            return self._rejected(provider, record_id, execution, f"Receipt verification failed safely ({type(exc).__name__}).")

        return ReceiptVerificationResult(
            verified=True,
            provider_name=provider,
            source_record_id=record_id,
            execution_id=execution,
            raw_observation=receipt.raw_observation,
            verification_method=receipt.verification_method,
            reasons=("Trusted provider receipt integrity and execution attribution checks passed.",),
        )

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
