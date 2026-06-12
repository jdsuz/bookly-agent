from __future__ import annotations

import json
from pathlib import Path

from bookly_agent.tools.orders import get_order_status
from bookly_agent.tools.refunds import initiate_refund


def test_get_order_status_found(temp_store: Path):
    result = get_order_status("ORD-1042", store_path=temp_store)
    assert result.ok
    assert result.data["order"]["status"] == "delivered"


def test_get_order_status_not_found(temp_store: Path):
    result = get_order_status("ORD-9999", store_path=temp_store)
    assert not result.ok
    assert result.error == "not_found"


def test_initiate_refund_success(temp_store: Path):
    result = initiate_refund("ORD-1042", "Damaged cover", store_path=temp_store)
    assert result.ok
    assert result.data["refund_id"].startswith("REF-")

    with temp_store.open(encoding="utf-8") as handle:
        store = json.load(handle)

    order = next(item for item in store["orders"] if item["order_id"] == "ORD-1042")
    assert order["refund_status"] == "completed"


def test_initiate_refund_ineligible(temp_store: Path):
    result = initiate_refund("ORD-2088", "Changed mind", store_path=temp_store)
    assert not result.ok
    assert result.error == "not_eligible"
