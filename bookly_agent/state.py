from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


MAX_HISTORY_TURNS = 12


@dataclass
class ConversationState:
    session_id: str
    active_flow: str | None = None
    flow_step: str | None = None
    slots: dict[str, Any] = field(default_factory=dict)
    pending_tool_result: dict[str, Any] | None = None
    history: list[dict[str, str]] = field(default_factory=list)

    def add_turn(self, role: str, content: str) -> None:
        self.history.append({"role": role, "content": content})
        if len(self.history) > MAX_HISTORY_TURNS:
            self.history = self.history[-MAX_HISTORY_TURNS:]

    def clear_flow(self) -> None:
        self.active_flow = None
        self.flow_step = None
        self.slots = {}
        self.pending_tool_result = None

    def start_flow(self, flow_name: str, step: str, **slots: Any) -> None:
        self.active_flow = flow_name
        self.flow_step = step
        self.slots = dict(slots)
        self.pending_tool_result = None


class SessionStore:
    def __init__(self) -> None:
        self._sessions: dict[str, ConversationState] = {}

    def get(self, session_id: str) -> ConversationState:
        if session_id not in self._sessions:
            self._sessions[session_id] = ConversationState(session_id=session_id)
        return self._sessions[session_id]

    def reset(self, session_id: str) -> None:
        self._sessions.pop(session_id, None)


DEFAULT_SESSION_STORE = SessionStore()
