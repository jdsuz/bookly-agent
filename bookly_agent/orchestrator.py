from __future__ import annotations

from bookly_agent.flows import FLOW_BY_NAME
from bookly_agent.llm.client import GeminiClient
from bookly_agent.policies import clarification_message, needs_clarification
from bookly_agent.router import Router
from bookly_agent.state import ConversationState, SessionStore
from bookly_agent.types import AgentResponse


INITIAL_FLOW_STEPS = {
    "order_status": "awaiting_order_id",
    "refund": "awaiting_order_id",
    "general_faq": "respond",
}


class Orchestrator:
    def __init__(
        self,
        *,
        session_store: SessionStore | None = None,
        router: Router | None = None,
        llm: GeminiClient | None = None,
    ) -> None:
        self.session_store = session_store or SessionStore()
        self.llm = llm or GeminiClient()
        self.router = router or Router(self.llm)

    def handle_turn(self, session_id: str, message: str) -> AgentResponse:
        state = self.session_store.get(session_id)
        cleaned = message.strip()
        if not cleaned:
            return AgentResponse(
                reply="I'm here to help. What can I do for you today?",
                session_id=session_id,
            )

        state.add_turn("user", cleaned)
        debug: dict = {}

        if state.active_flow:
            response = self._continue_flow(state, cleaned, debug)
        else:
            response = self._start_new_flow(state, cleaned, debug)

        state.add_turn("assistant", response.reply)
        response.session_id = session_id
        response.debug = debug
        return response

    def _continue_flow(self, state: ConversationState, message: str, debug: dict) -> AgentResponse:
        flow = FLOW_BY_NAME[state.active_flow]
        result = flow.step(state, message)
        debug["flow"] = state.active_flow
        debug["flow_step"] = state.flow_step

        if result.reply and not result.use_llm:
            if result.done:
                state.clear_flow()
            return AgentResponse(
                reply=result.reply,
                session_id=state.session_id,
                flow=flow.name,
                flow_step=state.flow_step,
                tool_context=result.tool_context,
            )

        if result.use_llm and result.tool_context:
            reply = self.llm.generate_response(message, result.tool_context, state.history)
            state.clear_flow()
            return AgentResponse(
                reply=reply,
                session_id=state.session_id,
                flow=flow.name,
                tool_context=result.tool_context,
            )

        if result.done:
            state.clear_flow()

        return AgentResponse(
            reply=result.reply or "How else can I help?",
            session_id=state.session_id,
            flow=flow.name,
            flow_step=state.flow_step,
            tool_context=result.tool_context,
        )

    def _start_new_flow(self, state: ConversationState, message: str, debug: dict) -> AgentResponse:
        route = self.router.classify(message, state.history)
        debug["route"] = {
            "intent": route.intent,
            "confidence": route.confidence,
            "slots": route.slots,
            "rationale": route.rationale,
        }

        if needs_clarification(route.intent, route.confidence):
            return AgentResponse(
                reply=clarification_message(route.intent, route.confidence),
                session_id=state.session_id,
                intent=route.intent,
            )

        flow_name = route.intent
        if flow_name not in FLOW_BY_NAME:
            return AgentResponse(
                reply=clarification_message("unknown", route.confidence),
                session_id=state.session_id,
                intent="unknown",
            )

        initial_step = INITIAL_FLOW_STEPS[flow_name]
        state.start_flow(flow_name, initial_step, **route.slots)
        flow = FLOW_BY_NAME[flow_name]
        result = flow.step(state, message)
        debug["flow"] = flow_name
        debug["flow_step"] = state.flow_step

        if result.reply and not result.use_llm:
            if result.done:
                state.clear_flow()
            return AgentResponse(
                reply=result.reply,
                session_id=state.session_id,
                intent=route.intent,
                flow=flow_name,
                flow_step=state.flow_step,
                tool_context=result.tool_context,
            )

        if result.use_llm and result.tool_context:
            reply = self.llm.generate_response(message, result.tool_context, state.history)
            state.clear_flow()
            return AgentResponse(
                reply=reply,
                session_id=state.session_id,
                intent=route.intent,
                flow=flow_name,
                tool_context=result.tool_context,
            )

        return AgentResponse(
            reply=result.reply or "How can I help you further?",
            session_id=state.session_id,
            intent=route.intent,
            flow=flow_name,
            flow_step=state.flow_step,
        )
