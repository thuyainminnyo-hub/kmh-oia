"""ModelGateway-backed Agent adapter for the existing OIARuntime Agent seam.

Model output is treated as untrusted structured data. The returned tool name
still passes through OIARuntime autonomy policy and GovernedTool authorization.
No provider SDK or network client is included here.
"""
import json
from uuid import uuid4

from src.agent import AgentDecision, AgentRequest
from src.ai_contracts import (
    AIRequest,
    BudgetSnapshot,
    DataClassification,
    TaskClass,
)
from src.model_gateway import ModelGateway
from src.trace import ExecutionContext


class GatewayBackedAgent:
    """Adapt an admitted model response into a strictly parsed AgentDecision."""

    def __init__(
        self,
        gateway: ModelGateway,
        *,
        route_id: str,
        max_output_tokens: int = 256,
        data_classification: DataClassification = DataClassification.INTERNAL,
        budget: BudgetSnapshot | None = None,
    ) -> None:
        if not isinstance(route_id, str) or not route_id.strip():
            raise ValueError("route_id is required")
        if isinstance(max_output_tokens, bool) or not isinstance(max_output_tokens, int) or max_output_tokens <= 0:
            raise ValueError("max_output_tokens must be a positive integer")
        if not isinstance(data_classification, DataClassification):
            raise ValueError("data_classification must be a DataClassification")
        self._gateway = gateway
        self._route_id = route_id
        self._max_output_tokens = max_output_tokens
        self._data_classification = data_classification
        self._budget = budget or BudgetSnapshot()

    def decide(self, request: AgentRequest) -> AgentDecision:
        if not isinstance(request, AgentRequest):
            raise ValueError("request must be an AgentRequest")
        if not isinstance(request.goal, str) or not request.goal.strip():
            raise ValueError("agent goal must be non-empty")
        payload = {
            "goal": request.goal,
            "context": request.context,
            "required_response_schema": {
                "tool_name": "string",
                "input_text": "string",
                "reason": "string",
            },
            "instruction": (
                "Return exactly one JSON object with exactly the three required "
                "string fields. Do not execute tools or claim that a tool ran."
            ),
        }
        input_text = json.dumps(payload, ensure_ascii=False, sort_keys=True)
        estimated_tokens = max(1, (len(input_text) + 3) // 4)
        if estimated_tokens > 8000:
            raise ValueError("agent context exceeds the hard input-token ceiling")

        model_request = AIRequest(
            request_id=f"agent:{uuid4()}",
            session_id="agent-session",
            task_class=TaskClass.RUNTIME_FEATURE,
            input_text=input_text,
            route_id=self._route_id,
            estimated_input_tokens=estimated_tokens,
            max_output_tokens=self._max_output_tokens,
            data_classification=self._data_classification,
        )
        result = self._gateway.execute(
            model_request,
            budget=self._budget,
            context=ExecutionContext.create("agent-session"),
        )
        if not result.accepted:
            raise PermissionError(f"model gateway denied agent request: {result.reason}")
        try:
            decoded = json.loads(result.text)
        except (TypeError, json.JSONDecodeError) as exc:
            raise ValueError("model response must be valid JSON") from exc
        if not isinstance(decoded, dict) or set(decoded) != {"tool_name", "input_text", "reason"}:
            raise ValueError("model response must contain exactly tool_name, input_text, and reason")
        if any(not isinstance(decoded[key], str) or not decoded[key].strip()
               for key in ("tool_name", "input_text", "reason")):
            raise ValueError("model response fields must be non-empty strings")
        return AgentDecision(
            tool_name=decoded["tool_name"],
            input_text=decoded["input_text"],
            reason=decoded["reason"],
        )
