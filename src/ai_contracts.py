"""Provider-neutral, deterministic admission contracts for AI tasks.

This module does not call a model or provider. It validates a proposed request
before any future gateway is allowed to perform inference.
"""
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from enum import Enum
from typing import Any, Mapping


class TaskClass(str, Enum):
    CODE_ASSIST = "code_assist"
    TEST_GENERATION = "test_generation"
    CODE_REVIEW = "code_review"
    RUNTIME_FEATURE = "runtime_feature"


class DataClassification(str, Enum):
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"


@dataclass(frozen=True)
class AIRequest:
    request_id: str
    session_id: str
    task_class: TaskClass
    input_text: str
    route_id: str
    estimated_input_tokens: int
    max_output_tokens: int
    estimated_cost_usd: Decimal = Decimal("0")
    data_classification: DataClassification = DataClassification.INTERNAL

    def __post_init__(self) -> None:
        for name in ("request_id", "session_id", "input_text", "route_id"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be a non-empty string")
        if not isinstance(self.task_class, TaskClass):
            raise ValueError("task_class must be a TaskClass")
        if not isinstance(self.data_classification, DataClassification):
            raise ValueError("data_classification must be a DataClassification")
        for name in ("estimated_input_tokens", "max_output_tokens"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise ValueError(f"{name} must be a non-negative integer")
        if self.max_output_tokens == 0:
            raise ValueError("max_output_tokens must be greater than zero")
        if not isinstance(self.estimated_cost_usd, Decimal):
            raise ValueError("estimated_cost_usd must be Decimal")
        if not self.estimated_cost_usd.is_finite() or self.estimated_cost_usd < 0:
            raise ValueError("estimated_cost_usd must be finite and non-negative")

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> "AIRequest":
        """Parse a JSON-like mapping with an exact allowlisted field set."""
        if not isinstance(payload, Mapping):
            raise ValueError("request payload must be a mapping")
        required = {
            "request_id", "session_id", "task_class", "input_text", "route_id",
            "estimated_input_tokens", "max_output_tokens",
        }
        optional = {"estimated_cost_usd", "data_classification"}
        keys = set(payload)
        missing = required - keys
        unknown = keys - required - optional
        if missing:
            raise ValueError("missing request fields: " + ", ".join(sorted(missing)))
        if unknown:
            raise ValueError("unknown request fields: " + ", ".join(sorted(map(str, unknown))))
        try:
            cost = Decimal(str(payload.get("estimated_cost_usd", "0")))
            task = TaskClass(payload["task_class"])
            classification = DataClassification(
                payload.get("data_classification", DataClassification.INTERNAL.value)
            )
        except (InvalidOperation, ValueError, TypeError) as exc:
            raise ValueError("invalid task, classification, or cost value") from exc
        return cls(
            request_id=payload["request_id"],
            session_id=payload["session_id"],
            task_class=task,
            input_text=payload["input_text"],
            route_id=payload["route_id"],
            estimated_input_tokens=payload["estimated_input_tokens"],
            max_output_tokens=payload["max_output_tokens"],
            estimated_cost_usd=cost,
            data_classification=classification,
        )


@dataclass(frozen=True)
class ModelRoute:
    route_id: str
    provider: str
    model: str
    free_tier: bool
    enabled: bool
    max_input_tokens: int
    max_output_tokens: int
    allowed_data_classifications: tuple[DataClassification, ...] = (
        DataClassification.PUBLIC,
        DataClassification.INTERNAL,
    )

    def __post_init__(self) -> None:
        for name in ("route_id", "provider", "model"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be a non-empty string")
        for name in ("max_input_tokens", "max_output_tokens"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
                raise ValueError(f"{name} must be a positive integer")
        if not isinstance(self.free_tier, bool) or not isinstance(self.enabled, bool):
            raise ValueError("free_tier and enabled must be booleans")


@dataclass(frozen=True)
class BudgetSnapshot:
    session_tokens_used: int = 0
    session_cost_usd: Decimal = Decimal("0")

    def __post_init__(self) -> None:
        if (
            isinstance(self.session_tokens_used, bool)
            or not isinstance(self.session_tokens_used, int)
            or self.session_tokens_used < 0
        ):
            raise ValueError("session_tokens_used must be a non-negative integer")
        if not isinstance(self.session_cost_usd, Decimal):
            raise ValueError("session_cost_usd must be Decimal")
        if not self.session_cost_usd.is_finite() or self.session_cost_usd < 0:
            raise ValueError("session_cost_usd must be finite and non-negative")


@dataclass(frozen=True)
class AIBudgetPolicy:
    max_input_chars: int = 20_000
    max_request_input_tokens: int = 8_000
    max_request_output_tokens: int = 2_000
    max_session_tokens: int = 20_000
    max_session_cost_usd: Decimal = Decimal("0")
    allow_paid_routes: bool = False

    def __post_init__(self) -> None:
        for name in (
            "max_input_chars", "max_request_input_tokens",
            "max_request_output_tokens", "max_session_tokens",
        ):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
                raise ValueError(f"{name} must be a positive integer")
        if not isinstance(self.max_session_cost_usd, Decimal):
            raise ValueError("max_session_cost_usd must be Decimal")
        if not self.max_session_cost_usd.is_finite() or self.max_session_cost_usd < 0:
            raise ValueError("max_session_cost_usd must be finite and non-negative")
        if not isinstance(self.allow_paid_routes, bool):
            raise ValueError("allow_paid_routes must be a boolean")


@dataclass(frozen=True)
class AdmissionDecision:
    allowed: bool
    reason: str
    route_id: str | None = None
    reserved_tokens: int = 0
    estimated_cost_usd: Decimal = Decimal("0")


class AIRequestGuardrail:
    """Fail-closed request, route, data-classification and budget gate."""

    def __init__(
        self,
        routes: tuple[ModelRoute, ...] | list[ModelRoute] = (),
        policy: AIBudgetPolicy | None = None,
    ) -> None:
        self._policy = policy or AIBudgetPolicy()
        self._routes: dict[str, ModelRoute] = {}
        for route in routes:
            if not isinstance(route, ModelRoute):
                raise ValueError("routes must contain ModelRoute values")
            if route.route_id in self._routes:
                raise ValueError("duplicate route_id")
            self._routes[route.route_id] = route

    def evaluate(
        self, request: AIRequest, budget: BudgetSnapshot | None = None
    ) -> AdmissionDecision:
        if not isinstance(request, AIRequest):
            return AdmissionDecision(False, "request must be a validated AIRequest")
        if budget is None:
            budget = BudgetSnapshot()
        if not isinstance(budget, BudgetSnapshot):
            return AdmissionDecision(False, "budget snapshot is unavailable or invalid")

        route = self._routes.get(request.route_id)
        if route is None:
            return AdmissionDecision(False, "route is not allowlisted")
        if not route.enabled:
            return AdmissionDecision(False, "route is disabled")
        if not route.free_tier and not self._policy.allow_paid_routes:
            return AdmissionDecision(False, "paid routes are disabled by policy")
        if request.data_classification not in route.allowed_data_classifications:
            return AdmissionDecision(False, "route is not approved for this data classification")
        if len(request.input_text) > self._policy.max_input_chars:
            return AdmissionDecision(False, "input exceeds character limit")
        if request.estimated_input_tokens > min(
            self._policy.max_request_input_tokens, route.max_input_tokens
        ):
            return AdmissionDecision(False, "input token limit exceeded")
        if request.max_output_tokens > min(
            self._policy.max_request_output_tokens, route.max_output_tokens
        ):
            return AdmissionDecision(False, "output token limit exceeded")
        if route.free_tier and request.estimated_cost_usd != Decimal("0"):
            return AdmissionDecision(False, "free-tier route must have zero estimated cost")

        reserve = request.estimated_input_tokens + request.max_output_tokens
        if budget.session_tokens_used + reserve > self._policy.max_session_tokens:
            return AdmissionDecision(False, "session token budget exceeded")
        if budget.session_cost_usd + request.estimated_cost_usd > self._policy.max_session_cost_usd:
            return AdmissionDecision(False, "session cost budget exceeded")

        return AdmissionDecision(
            True,
            "request admitted; provider execution is not performed by this guardrail",
            route_id=route.route_id,
            reserved_tokens=reserve,
            estimated_cost_usd=request.estimated_cost_usd,
        )
