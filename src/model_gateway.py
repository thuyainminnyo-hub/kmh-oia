"""Provider-neutral model gateway with deterministic preflight admission.

The gateway deliberately knows no HTTP client, API key, provider SDK or hosted
service. Providers are injected behind a small protocol; tests use a fake
provider. A live adapter requires separate security, privacy, cost and
operational review before registration.
"""
from dataclasses import dataclass
from decimal import Decimal
from typing import Protocol

from src.ai_contracts import (
    AIRequest,
    AIRequestGuardrail,
    AdmissionDecision,
    BudgetSnapshot,
    ModelRoute,
)
from src.trace import ExecutionContext, TraceEvent, Tracer


@dataclass(frozen=True)
class ModelUsage:
    input_tokens: int
    output_tokens: int
    cost_usd: Decimal = Decimal("0")

    def __post_init__(self) -> None:
        for name in ("input_tokens", "output_tokens"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise ValueError(f"{name} must be a non-negative integer")
        if not isinstance(self.cost_usd, Decimal):
            raise ValueError("cost_usd must be Decimal")
        if not self.cost_usd.is_finite() or self.cost_usd < 0:
            raise ValueError("cost_usd must be finite and non-negative")


@dataclass(frozen=True)
class ModelResponse:
    text: str
    usage: ModelUsage


class ModelProvider(Protocol):
    """Adapter contract; implementations perform the actual inference."""

    def generate(self, request: AIRequest) -> ModelResponse: ...


@dataclass(frozen=True)
class GatewayResult:
    accepted: bool
    reason: str
    text: str = ""
    route_id: str | None = None
    usage: ModelUsage | None = None


class ModelGateway:
    """Runs only pre-admitted requests through explicitly registered adapters."""

    def __init__(
        self,
        guardrail: AIRequestGuardrail,
        routes: tuple[ModelRoute, ...] | list[ModelRoute],
        providers: dict[str, ModelProvider],
        tracer: Tracer | None = None,
    ) -> None:
        if not isinstance(guardrail, AIRequestGuardrail):
            raise ValueError("a valid AIRequestGuardrail is required")
        self._guardrail = guardrail
        self._routes = {route.route_id: route for route in routes}
        if len(self._routes) != len(routes):
            raise ValueError("duplicate gateway route_id")
        if set(providers) - set(self._routes):
            raise ValueError("provider registered for an unknown route")
        self._providers = dict(providers)
        self._tracer = tracer

    def execute(
        self,
        request: AIRequest,
        budget: BudgetSnapshot | None = None,
        context: ExecutionContext | None = None,
    ) -> GatewayResult:
        decision = self._guardrail.evaluate(request, budget)
        if not decision.allowed:
            self._emit(context, "model.admission", "denied", "policy_denied")
            return GatewayResult(False, decision.reason)

        route = self._routes.get(request.route_id)
        provider = self._providers.get(request.route_id)
        if route is None or provider is None:
            self._emit(context, "model.route", "denied", "route_unavailable")
            return GatewayResult(False, "no provider adapter is registered for the admitted route")

        self._emit(context, "model.inference", "started", None)
        try:
            response = provider.generate(request)
        except Exception:
            self._emit(context, "model.inference", "error", "provider_error")
            return GatewayResult(False, "provider execution failed")

        if not isinstance(response, ModelResponse):
            self._emit(context, "model.response", "denied", "invalid_response")
            return GatewayResult(False, "provider returned an invalid response contract")
        if not isinstance(response.text, str) or not response.text.strip():
            self._emit(context, "model.response", "denied", "empty_response")
            return GatewayResult(False, "provider returned an empty response")
        if not isinstance(response.usage, ModelUsage):
            self._emit(context, "model.response", "denied", "invalid_usage")
            return GatewayResult(False, "provider returned invalid usage data")
        if response.usage.input_tokens > request.estimated_input_tokens:
            self._emit(context, "model.response", "denied", "input_usage_exceeded")
            return GatewayResult(False, "provider input usage exceeded the admitted estimate")
        if response.usage.output_tokens > request.max_output_tokens:
            self._emit(context, "model.response", "denied", "output_usage_exceeded")
            return GatewayResult(False, "provider output usage exceeded the admitted limit")
        if route.free_tier and response.usage.cost_usd != Decimal("0"):
            self._emit(context, "model.response", "denied", "unexpected_cost")
            return GatewayResult(False, "free-tier route reported a non-zero cost")
        if response.usage.cost_usd > request.estimated_cost_usd:
            self._emit(context, "model.response", "denied", "cost_estimate_exceeded")
            return GatewayResult(False, "actual cost exceeded the admitted estimate")

        self._emit(context, "model.response", "ok", None)
        return GatewayResult(
            True,
            "provider response passed gateway contract checks",
            text=response.text,
            route_id=route.route_id,
            usage=response.usage,
        )

    def _emit(
        self,
        context: ExecutionContext | None,
        stage: str,
        status: str,
        error_category: str | None,
    ) -> None:
        if self._tracer is None or context is None:
            return
        self._tracer.emit(TraceEvent(
            stage=stage,
            status=status,
            metadata=context.as_metadata(),
            error_category=error_category,
        ))
