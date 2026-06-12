from __future__ import annotations

from bookly_agent.flows.base import BaseFlow, FlowStepResult
from bookly_agent.policies import extract_order_id, validate_order_id
from bookly_agent.state import ConversationState
from bookly_agent.tools.orders import get_order_status


class OrderStatusFlow(BaseFlow):
    name = "order_status"

    def step(self, state: ConversationState, message: str) -> FlowStepResult:
        step = state.flow_step or "awaiting_order_id"

        if step == "awaiting_order_id":
            order_id = state.slots.get("order_id") or extract_order_id(message)
            if not order_id:
                return FlowStepResult(
                    reply="I'd be happy to check that for you. What's your order number? (e.g. ORD-1042)",
                )

            error = validate_order_id(order_id)
            if error:
                return FlowStepResult(reply=error)

            state.slots["order_id"] = order_id
            state.flow_step = "lookup"
            return self.step(state, message)

        if step == "lookup":
            order_id = state.slots["order_id"]
            result = get_order_status(order_id)
            if not result.ok:
                state.clear_flow()
                if result.error == "not_found":
                    return FlowStepResult(
                        reply=(
                            f"I couldn't find order {order_id}. "
                            "Please check the number and try again, or contact us with the email used at checkout."
                        ),
                        done=True,
                    )
                return FlowStepResult(reply="That order number doesn't look valid. Please try again.", done=True)

            order = result.data["order"]
            state.pending_tool_result = {"action": "order_status", "order": order}
            state.flow_step = "respond"
            return FlowStepResult(
                tool_context=state.pending_tool_result,
                use_llm=True,
                done=True,
            )

        return FlowStepResult(reply="Something went wrong. Let's start over — what's your order number?")
