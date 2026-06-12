from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from bookly_agent.config import mock_data_path
from bookly_agent.tools.base import ToolResult
from bookly_agent.tools.orders import get_order_status, normalize_order_id


def _load_store(path: Path | None = None) -> dict:
    data_path = path or mock_data_path()
    with data_path.open(encoding="utf-8") as handle:
        return json.load(handle)


def _save_store(store: dict, path: Path | None = None) -> None:
    data_path = path or mock_data_path()
    with data_path.open("w", encoding="utf-8") as handle:
        json.dump(store, handle, indent=2)
        handle.write("\n")


def _next_refund_id(store: dict) -> str:
    existing = [entry.get("refund_id", "") for entry in store.get("refunds", [])]
    numbers = []
    for refund_id in existing:
        if refund_id.startswith("REF-"):
            try:
                numbers.append(int(refund_id.split("-", 1)[1]))
            except ValueError:
                continue
    next_number = max(numbers, default=990) + 1
    return f"REF-{next_number}"


def initiate_refund(
    order_id: str,
    reason: str,
    *,
    store_path: Path | None = None,
    persist: bool = True,
) -> ToolResult:
    normalized = normalize_order_id(order_id)
    lookup = get_order_status(normalized, store_path=store_path)
    if not lookup.ok:
        return lookup

    order = lookup.data["order"]
    if order.get("refund_status") == "completed":
        return ToolResult.failure(
            "already_refunded",
            order_id=normalized,
            refund_id=order.get("refund_id"),
        )

    if not order.get("refund_eligible"):
        return ToolResult.failure(
            "not_eligible",
            order_id=normalized,
            status=order.get("status"),
        )

    store = _load_store(store_path)
    refund_id = _next_refund_id(store)
    refund_record = {
        "refund_id": refund_id,
        "order_id": normalized,
        "reason": reason.strip(),
        "amount": order.get("total"),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    for entry in store.get("orders", []):
        if entry["order_id"].upper() == normalized:
            entry["refund_status"] = "completed"
            entry["refund_id"] = refund_id
            entry["refund_eligible"] = False
            break

    store.setdefault("refunds", []).append(refund_record)

    if persist:
        _save_store(store, store_path)

    return ToolResult.success(
        refund_id=refund_id,
        order_id=normalized,
        amount=order.get("total"),
        reason=reason.strip(),
    )
