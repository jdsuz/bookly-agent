from __future__ import annotations

from bookly_agent.flows.order_status import OrderStatusFlow
from bookly_agent.flows.refund import RefundFlow
from bookly_agent.state import ConversationState


def test_order_status_flow_multiturn():
    state = ConversationState(session_id="test")
    state.start_flow("order_status", "awaiting_order_id")
    flow = OrderStatusFlow()

    first = flow.step(state, "Where is my package?")
    assert "order number" in first.reply.lower()

    second = flow.step(state, "ORD-1042")
    assert second.use_llm
    assert second.tool_context["order"]["order_id"] == "ORD-1042"


def test_refund_flow_requires_confirmation():
    state = ConversationState(session_id="test")
    state.start_flow("refund", "awaiting_order_id")
    flow = RefundFlow()

    flow.step(state, "ORD-1042")
    prompt = flow.step(state, "Book arrived damaged")
    assert "go ahead" in prompt.reply.lower()

    cancelled = flow.step(state, "no thanks")
    assert cancelled.done
    assert "cancelled" in cancelled.reply.lower()
