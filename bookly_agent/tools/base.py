from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ToolResult:
    ok: bool
    data: dict[str, Any] = field(default_factory=dict)
    error: str | None = None

    @classmethod
    def success(cls, **data: Any) -> ToolResult:
        return cls(ok=True, data=dict(data))

    @classmethod
    def failure(cls, error: str, **data: Any) -> ToolResult:
        return cls(ok=False, data=dict(data), error=error)
