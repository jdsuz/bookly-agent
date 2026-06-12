from __future__ import annotations

import os
from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parent


def env_bool(name: str, default: bool = False) -> bool:
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def gemini_api_key() -> str | None:
    key = os.environ.get("GEMINI_API_KEY")
    if key:
        return str(key).strip() or None
    return None


def gemini_model() -> str:
    return os.environ.get("BOOKLY_AGENT_MODEL", "gemini-2.5-flash").strip() or "gemini-2.5-flash"


def llm_timeout_seconds() -> int:
    return int(os.environ.get("BOOKLY_AGENT_TIMEOUT_SECONDS", "15"))


def mock_llm_enabled() -> bool:
    return env_bool("BOOKLY_AGENT_MOCK_LLM", False)


def mock_data_path() -> Path:
    override = os.environ.get("BOOKLY_AGENT_DATA_PATH")
    if override:
        return Path(override)
    return PACKAGE_ROOT / "data" / "mock_orders.json"
