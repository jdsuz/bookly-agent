from __future__ import annotations

import json
from pathlib import Path

from flask import Blueprint, Response, current_app, jsonify, request, send_from_directory
from importlib.metadata import distribution

from bookly_agent.orchestrator import Orchestrator


def _resolve_widget_dir() -> Path:
    """Prefer editable-install source assets over stale site-packages copies."""
    fallback = Path(__file__).resolve().parent / "widget"
    try:
        direct_url = Path(distribution("bookly-agent")._path) / "direct_url.json"
        if direct_url.is_file():
            data = json.loads(direct_url.read_text(encoding="utf-8"))
            url = data.get("url", "")
            if url.startswith("file://"):
                source_widget = Path(url[7:]) / "bookly_agent" / "server" / "widget"
                if (source_widget / "support-widget.js").is_file():
                    return source_widget
    except Exception:
        pass
    return fallback


WIDGET_DIR = _resolve_widget_dir()

_orchestrator: Orchestrator | None = None


def get_orchestrator() -> Orchestrator:
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = Orchestrator()
    return _orchestrator


def create_blueprint(url_prefix: str = "/api/support") -> Blueprint:
    bp = Blueprint("bookly_support", __name__, url_prefix=url_prefix)

    @bp.post("/chat")
    def chat():
        data = request.get_json(silent=True) or {}
        session_id = str(data.get("session_id") or "").strip()
        message = str(data.get("message") or "").strip()

        if not session_id:
            return jsonify({"error": "session_id is required"}), 400
        if not message:
            return jsonify({"error": "message is required"}), 400

        response = get_orchestrator().handle_turn(session_id, message)
        payload = response.to_dict()
        if not current_app.debug:
            payload.pop("debug", None)
        return jsonify(payload)

    @bp.post("/reset")
    def reset_session():
        data = request.get_json(silent=True) or {}
        session_id = str(data.get("session_id") or "").strip()
        if not session_id:
            return jsonify({"error": "session_id is required"}), 400
        get_orchestrator().session_store.reset(session_id)
        return jsonify({"ok": True})

    @bp.get("/widget/<path:filename>")
    def widget_assets(filename: str):
        response = send_from_directory(WIDGET_DIR, filename)
        if filename.endswith((".js", ".css")):
            response.cache_control.no_cache = True
            response.cache_control.must_revalidate = True
        return response

    return bp


def widget_snippet(chat_url: str = "/api/support/chat", asset_prefix: str = "/api/support/widget") -> str:
    version = "3"
    return (
        f'<link rel="stylesheet" href="{asset_prefix}/support-widget.css?v={version}" />'
        f'<script src="{asset_prefix}/support-widget.js?v={version}" '
        f'data-chat-url="{chat_url}" defer></script>'
    )
