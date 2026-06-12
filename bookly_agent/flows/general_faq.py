from __future__ import annotations

from bookly_agent.flows.base import BaseFlow, FlowStepResult
from bookly_agent.state import ConversationState

FAQ_SNIPPETS = {
    "shipping": (
        "Bookly offers free standard shipping on orders over $35 (5–7 business days). "
        "Express shipping (2–3 business days) is $9.99. International shipping is not available yet."
    ),
    "returns": (
        "You can request a return within 30 days of delivery for a full refund. "
        "Items must be unused and in original packaging. Start a return here in chat or email support@bookly.com."
    ),
    "password": (
        "To reset your password, go to bookly.com/login and click 'Forgot password'. "
        "We'll email a reset link within a few minutes. Check spam if you don't see it."
    ),
    "policies": (
        "Bookly's price-match policy covers major retailers within 7 days of purchase. "
        "Gift cards are non-refundable. Pre-orders can be cancelled before shipment."
    ),
}

TOPIC_KEYWORDS = {
    "shipping": ("ship", "shipping", "delivery", "arrive", "tracking"),
    "returns": ("return", "policy", "exchange"),
    "password": ("password", "login", "sign in", "reset"),
    "policies": ("policy", "policies", "price match", "gift card", "pre-order"),
}


def detect_faq_topic(message: str, topic_hint: str | None = None) -> str:
    if topic_hint and topic_hint in FAQ_SNIPPETS:
        return topic_hint

    lowered = message.lower()
    for topic, keywords in TOPIC_KEYWORDS.items():
        if any(keyword in lowered for keyword in keywords):
            return topic
    return "policies"


class GeneralFaqFlow(BaseFlow):
    name = "general_faq"

    def step(self, state: ConversationState, message: str) -> FlowStepResult:
        topic = detect_faq_topic(message, state.slots.get("topic"))
        snippet = FAQ_SNIPPETS[topic]
        state.pending_tool_result = {
            "action": "general_faq",
            "topic": topic,
            "snippet": snippet,
            "question": message,
        }
        return FlowStepResult(
            tool_context=state.pending_tool_result,
            use_llm=True,
            done=True,
        )
