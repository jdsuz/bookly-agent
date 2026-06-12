from __future__ import annotations

from bookly_agent.flows.base import BaseFlow, FlowStepResult
from bookly_agent.policies import extract_order_id, is_affirmative, is_negative, validate_order_id
from bookly_agent.state import ConversationState
from bookly_agent.tools.orders import get_order_status
from bookly_agent.tools.refunds import initiate_refund


class RefundFlow(BaseFlow):
    name = "refund"

    def step(self, state: ConversationState, message: str) -> FlowStepResult:
        step = state.flow_step or "awaiting_order_id"

        if step == "awaiting_order_id":
            order_id = state.slots.get("order_id") or extract_order_id(message)
            if not order_id:
                return FlowStepResult(
                    reply="I can help with a refund. What's your order number? (e.g. ORD-1042)",
                )

            error = validate_order_id(order_id)
            if error:
                return FlowStepResult(reply=error)

            state.slots["order_id"] = order_id
            state.flow_step = "awaiting_reason"
            if state.slots.get("reason"):
                return self.step(state, message)
            return FlowStepResult(
                reply=f"Got it — {order_id}. What's the reason for your refund request?",
            )

        if step == "awaiting_reason":
            reason = message.strip()
            if len(reason) < 3 or reason.upper() == state.slots.get("order_id"):
                return FlowStepResult(
                    reply="Please briefly describe why you'd like a refund (e.g. damaged item, wrong book).",
                )

            state.slots["reason"] = reason
            state.flow_step = "confirm"

            lookup = get_order_status(state.slots["order_id"])
            if not lookup.ok:
                state.clear_flow()
                return FlowStepResult(
                    reply=f"I couldn't find order {state.slots['order_id']}. Please verify the order number.",
                    done=True,
                )

            order = lookup.data["order"]
            if not order.get("refund_eligible"):
                state.clear_flow()
                title = order["items"][0]["title"] if order.get("items") else "your order"
                if order.get("refund_status") == "completed":
                    return FlowStepResult(
                        reply=(
                            f"A refund has already been processed for {title} "
                            f"(refund ID {order.get('refund_id', 'on file')})."
                        ),
                        done=True,
                    )
                return FlowStepResult(
                    reply=(
                        f"Order {order['order_id']} ({title}) is currently {order['status'].replace('_', ' ')} "
                        "and isn't eligible for a refund yet. Once delivered, you have 30 days to request a return."
                    ),
                    done=True,
                    tool_context={"action": "refund_ineligible", "order": order},
                    use_llm=True,
                )

            title = order["items"][0]["title"] if order.get("items") else "your item"
            total = order.get("total", 0)
            state.pending_tool_result = {"action": "refund_confirm", "order": order, "reason": reason}
            return FlowStepResult(
                reply=(
                    f"I can start a refund of ${total:.2f} for \"{title}\" on {order['order_id']}. "
                    "Should I go ahead?"
                ),
            )

        if step == "confirm":
            if is_negative(message):
                state.clear_flow()
                return FlowStepResult(
                    reply="No problem — I've cancelled the refund request. Let me know if you need anything else.",
                    done=True,
                )
            if not is_affirmative(message):
                return FlowStepResult(
                    reply="Please reply yes to confirm the refund, or no to cancel.",
                )

            state.flow_step = "execute"
            return self.step(state, message)

        if step == "execute":
            result = initiate_refund(
                state.slots["order_id"],
                state.slots.get("reason", "Customer request"),
            )
            state.flow_step = "respond"
            if not result.ok:
                state.clear_flow()
                return FlowStepResult(
                    reply=f"I wasn't able to process that refund: {result.error.replace('_', ' ')}.",
                    done=True,
                )

            state.pending_tool_result = {
                "action": "refund_completed",
                **result.data,
            }
            return FlowStepResult(
                tool_context=state.pending_tool_result,
                use_llm=True,
                done=True,
            )

        return FlowStepResult(reply="Let's start over — what order would you like to refund?")
