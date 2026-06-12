from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from bookly_agent.llm.client import GeminiClient
from bookly_agent.orchestrator import Orchestrator
from bookly_agent.state import SessionStore


@pytest.fixture
def temp_store(tmp_path: Path) -> Path:
    source = Path(__file__).resolve().parent.parent / "data" / "mock_orders.json"
    target = tmp_path / "mock_orders.json"
    shutil.copy(source, target)
    return target


@pytest.fixture(autouse=True)
def use_temp_store(monkeypatch: pytest.MonkeyPatch, temp_store: Path):
    monkeypatch.setenv("BOOKLY_AGENT_DATA_PATH", str(temp_store))
    monkeypatch.setenv("BOOKLY_AGENT_MOCK_LLM", "true")


@pytest.fixture
def orchestrator() -> Orchestrator:
    return Orchestrator(
        session_store=SessionStore(),
        llm=GeminiClient(use_mock=True),
    )
