from __future__ import annotations

import json
import re
from pathlib import Path

from bookly_agent.config import mock_data_path
from bookly_agent.tools.base import ToolResult

ORDER_ID_PATTERN = re.compile(r"^ORD-\d{4}$", re.IGNORECASE)


def normalize_order_id(order_id: str) -> str:
    return order_id.strip().upper()


def is_valid_order_id(order_id: str) -> bool:
    return bool(ORDER_ID_PATTERN.match(normalize_order_id(order_id)))


def _load_store(path: Path | None = None) -> dict:
    data_path = path or mock_data_path()
    with data_path.open(encoding="utf-8") as handle:
        return json.load(handle)


def get_order_status(order_id: str, *, store_path: Path | None = None) -> ToolResult:
    normalized = normalize_order_id(order_id)
    if not is_valid_order_id(normalized):
        return ToolResult.failure(
            "invalid_order_id",
            order_id=normalized,
        )

    store = _load_store(store_path)
    for order in store.get("orders", []):
        if order["order_id"].upper() == normalized:
            return ToolResult.success(order=order)

    return ToolResult.failure("not_found", order_id=normalized)
