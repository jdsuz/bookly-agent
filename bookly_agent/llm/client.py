from __future__ import annotations

import json
import logging
import re
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Callable

from bookly_agent.config import gemini_api_key, gemini_model, llm_timeout_seconds, mock_llm_enabled
from bookly_agent.llm.prompts import RESPONSE_SYSTEM, ROUTER_RESPONSE_SCHEMA, ROUTER_SYSTEM

logger = logging.getLogger("bookly_agent.llm")

GEMINI_API_BASE = "https://generativelanguage.googleapis.com/v1beta/models"

GenerateContentFn = Callable[..., dict]


def _response_text(payload: dict) -> str:
    candidates = payload.get("candidates") or []
    if not candidates:
        return ""

    content = candidates[0].get("content") or {}
    parts = content.get("parts") or []
    text_parts = [str(part.get("text") or "") for part in parts if part.get("text")]
    return "".join(text_parts).strip()


def _generate_content(
    *,
    system_instruction: str,
    user_text: str,
    temperature: float,
    response_schema: dict | None = None,
    api_key: str,
    model: str,
) -> dict:
    body: dict[str, Any] = {
        "systemInstruction": {"parts": [{"text": system_instruction}]},
        "contents": [{"role": "user", "parts": [{"text": user_text}]}],
        "generationConfig": {"temperature": temperature},
    }
    if response_schema is not None:
        body["generationConfig"]["responseMimeType"] = "application/json"
        body["generationConfig"]["responseSchema"] = response_schema

    encoded_model = urllib.parse.quote(model, safe="")
    url = f"{GEMINI_API_BASE}/{encoded_model}:generateContent?key={urllib.parse.quote(api_key, safe='')}"
    request = urllib.request.Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=llm_timeout_seconds()) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Gemini request failed: {detail}") from error


def _mock_route_intent(message: str) -> dict[str, Any]:
    lowered = message.lower()
    slots: dict[str, str] = {}
    order_match = re.search(r"ORD-\d{4}", message, re.IGNORECASE)
    if order_match:
        slots["order_id"] = order_match.group(0).upper()

    if any(word in lowered for word in ("refund", "return", "money back")):
        return {"intent": "refund", "confidence": 0.9, "slots": slots, "rationale": "mock"}
    if any(word in lowered for word in ("order", "status", "where", "tracking", "shipped")):
        return {"intent": "order_status", "confidence": 0.88, "slots": slots, "rationale": "mock"}
    if any(word in lowered for word in ("ship", "password", "policy", "login")):
        return {"intent": "general_faq", "confidence": 0.85, "slots": slots, "rationale": "mock"}
    if len(lowered.split()) <= 3:
        return {"intent": "unknown", "confidence": 0.4, "slots": slots, "rationale": "mock"}
    return {"intent": "general_faq", "confidence": 0.7, "slots": slots, "rationale": "mock"}


def _mock_generate_response(user_text: str) -> str:
    if "refund_completed" in user_text:
        return "Your refund has been initiated. You should see it on your statement within 5–7 business days."
    if "order_status" in user_text:
        return "Here's the latest on your order based on our records."
    return "Happy to help with your Bookly question. Let me know if you need anything else."


class GeminiClient:
    def __init__(
        self,
        *,
        api_key: str | None = None,
        model: str | None = None,
        use_mock: bool | None = None,
        generate_content: GenerateContentFn | None = None,
    ) -> None:
        self.api_key = api_key if api_key is not None else gemini_api_key()
        self.model = model or gemini_model()
        self.use_mock = mock_llm_enabled() if use_mock is None else use_mock
        self._generate_content = generate_content or _generate_content

    def route_intent(self, message: str, history: list[dict[str, str]]) -> dict[str, Any]:
        if self.use_mock or not self.api_key:
            return _mock_route_intent(message)

        history_text = "\n".join(f"{turn['role']}: {turn['content']}" for turn in history[-6:])
        user_text = f"Recent conversation:\n{history_text}\n\nLatest message:\n{message.strip()}"

        try:
            payload = self._generate_content(
                system_instruction=ROUTER_SYSTEM,
                user_text=user_text,
                temperature=0.1,
                response_schema=ROUTER_RESPONSE_SCHEMA,
                api_key=self.api_key,
                model=self.model,
            )
            text = _response_text(payload)
            parsed = json.loads(text)
            if not isinstance(parsed, dict):
                raise ValueError("Router response must be a JSON object")
            parsed.setdefault("slots", {})
            return parsed
        except Exception as error:
            logger.warning("route_intent_failed error=%s", error)
            return _mock_route_intent(message)

    def generate_response(
        self,
        message: str,
        tool_context: dict[str, Any],
        history: list[dict[str, str]],
    ) -> str:
        if self.use_mock or not self.api_key:
            return _mock_generate_response(json.dumps(tool_context))

        history_text = "\n".join(f"{turn['role']}: {turn['content']}" for turn in history[-6:])
        user_text = (
            f"Conversation:\n{history_text}\n\n"
            f"Customer message:\n{message.strip()}\n\n"
            f"Tool/policy context (JSON):\n{json.dumps(tool_context, indent=2)}"
        )

        try:
            payload = self._generate_content(
                system_instruction=RESPONSE_SYSTEM,
                user_text=user_text,
                temperature=0.4,
                response_schema=None,
                api_key=self.api_key,
                model=self.model,
            )
            text = _response_text(payload)
            if text:
                return text
        except Exception as error:
            logger.warning("generate_response_failed error=%s", error)

        return _mock_generate_response(json.dumps(tool_context))
