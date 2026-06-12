from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from bookly_agent.llm.client import GeminiClient
from bookly_agent.policies import extract_order_id


@dataclass
class RouteResult:
    intent: str
    confidence: float
    slots: dict[str, Any] = field(default_factory=dict)
    rationale: str = ""


class Router:
    def __init__(self, llm: GeminiClient | None = None) -> None:
        self.llm = llm or GeminiClient()

    def classify(self, message: str, history: list[dict[str, str]]) -> RouteResult:
        raw = self.llm.route_intent(message, history)
        slots = dict(raw.get("slots") or {})

        if not slots.get("order_id"):
            extracted = extract_order_id(message)
            if extracted:
                slots["order_id"] = extracted

        return RouteResult(
            intent=str(raw.get("intent") or "unknown"),
            confidence=float(raw.get("confidence") or 0.0),
            slots=slots,
            rationale=str(raw.get("rationale") or ""),
        )
