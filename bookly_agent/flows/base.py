from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class FlowStepResult:
    reply: str | None = None
    done: bool = False
    tool_context: dict[str, Any] | None = None
    use_llm: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)


class BaseFlow:
    name: str = "base"

    def step(self, state, message: str) -> FlowStepResult:  # noqa: ANN001
        raise NotImplementedError
