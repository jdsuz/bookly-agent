from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class AgentResponse:
    reply: str
    session_id: str
    intent: str | None = None
    flow: str | None = None
    flow_step: str | None = None
    tool_context: dict[str, Any] | None = None
    debug: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "reply": self.reply,
            "session_id": self.session_id,
            "intent": self.intent,
            "flow": self.flow,
            "flow_step": self.flow_step,
            "tool_context": self.tool_context,
            "debug": self.debug,
        }
