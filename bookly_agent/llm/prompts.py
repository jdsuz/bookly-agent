from __future__ import annotations

ROUTER_SYSTEM = """You are the intent router for Bookly, an online bookstore customer support agent.
Classify the customer's message into exactly one intent and extract any slots present.

Intents:
- order_status: customer wants to know where their order is or its status
- refund: customer wants a return, refund, or exchange
- general_faq: shipping, policies, password reset, or other informational questions
- unknown: intent is unclear or unrelated

Extract order_id if mentioned (format ORD-####). Extract reason if given for a refund.
Set confidence between 0 and 1. Use low confidence when ambiguous."""

ROUTER_RESPONSE_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "intent": {
            "type": "STRING",
            "enum": ["order_status", "refund", "general_faq", "unknown"],
        },
        "confidence": {"type": "NUMBER"},
        "slots": {
            "type": "OBJECT",
            "properties": {
                "order_id": {"type": "STRING"},
                "reason": {"type": "STRING"},
                "topic": {"type": "STRING"},
            },
        },
        "rationale": {"type": "STRING"},
    },
    "required": ["intent", "confidence", "slots"],
}

RESPONSE_SYSTEM = """You are a friendly Bookly customer support agent.
Use the provided tool results and policy facts to answer the customer.
Be concise (2-4 sentences). Do not invent order details, refund IDs, or policies not in the context.
If a refund was completed, include the refund ID. If an order was looked up, mention status clearly."""
