from __future__ import annotations

import re

from bookly_agent.tools.orders import is_valid_order_id

CONFIDENCE_THRESHOLD = 0.65

CLARIFY_LOW_CONFIDENCE = (
    "I want to make sure I help with the right thing. "
    "Are you asking about an order status, a return or refund, or a general policy question?"
)

CLARIFY_AMBIGUOUS_INTENT = (
    "Just to confirm — would you like to check an order's status, or start a return/refund?"
)

INVALID_ORDER_ID_MESSAGE = (
    "That doesn't look like a valid order number. Bookly order IDs look like ORD-1042. "
    "Could you double-check and send it again?"
)

AFFIRMATIVE_PATTERN = re.compile(
    r"\b(yes|yeah|yep|confirm|sure|ok|okay|go ahead|please do)\b",
    re.IGNORECASE,
)
NEGATIVE_PATTERN = re.compile(
    r"\b(no|nope|cancel|never mind|nevermind|stop)\b",
    re.IGNORECASE,
)


def needs_clarification(intent: str, confidence: float) -> bool:
    if intent == "unknown":
        return True
    return confidence < CONFIDENCE_THRESHOLD


def clarification_message(intent: str, confidence: float) -> str:
    if intent == "unknown":
        return CLARIFY_LOW_CONFIDENCE
    if confidence < CONFIDENCE_THRESHOLD:
        return CLARIFY_AMBIGUOUS_INTENT
    return CLARIFY_LOW_CONFIDENCE


def validate_order_id(order_id: str) -> str | None:
    if not is_valid_order_id(order_id):
        return INVALID_ORDER_ID_MESSAGE
    return None


def is_affirmative(message: str) -> bool:
    return bool(AFFIRMATIVE_PATTERN.search(message.strip()))


def is_negative(message: str) -> bool:
    return bool(NEGATIVE_PATTERN.search(message.strip()))


def extract_order_id(message: str) -> str | None:
    match = re.search(r"ORD-\d{4}", message, re.IGNORECASE)
    if match:
        return match.group(0).upper()
    return None
