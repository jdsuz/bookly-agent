from __future__ import annotations

from bookly_agent.orchestrator import Orchestrator


def test_clarifying_question_on_ambiguous_intent(orchestrator: Orchestrator):
    response = orchestrator.handle_turn("sess-1", "help")
    assert "order status" in response.reply.lower() or "refund" in response.reply.lower()


def test_refund_multiturn_conversation(orchestrator: Orchestrator):
    session = "sess-refund"

    first = orchestrator.handle_turn(session, "I need a refund")
    assert "order number" in first.reply.lower()

    second = orchestrator.handle_turn(session, "ORD-1042")
    assert "reason" in second.reply.lower()

    third = orchestrator.handle_turn(session, "Wrong item shipped")
    assert "go ahead" in third.reply.lower() or "$" in third.reply

    fourth = orchestrator.handle_turn(session, "yes")
    assert fourth.tool_context is not None
    assert fourth.tool_context.get("action") == "refund_completed"


def test_order_status_tool_use(orchestrator: Orchestrator):
    response = orchestrator.handle_turn("sess-order", "Track order ORD-2088")
    assert response.tool_context is not None
    assert response.tool_context["order"]["status"] == "in_transit"


def test_general_faq(orchestrator: Orchestrator):
    response = orchestrator.handle_turn("sess-faq", "How does shipping work?")
    assert response.tool_context is not None
    assert response.tool_context["topic"] == "shipping"
