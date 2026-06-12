from __future__ import annotations

from pathlib import Path

from flask import Blueprint, Response, current_app, jsonify, request, send_from_directory

from bookly_agent.orchestrator import Orchestrator

WIDGET_DIR = Path(__file__).resolve().parent / "widget"

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
        return send_from_directory(WIDGET_DIR, filename)

    return bp


def widget_snippet(chat_url: str = "/api/support/chat", asset_prefix: str = "/api/support/widget") -> str:
    return (
        f'<link rel="stylesheet" href="{asset_prefix}/support-widget.css" />'
        f'<script src="{asset_prefix}/support-widget.js" '
        f'data-chat-url="{chat_url}" defer></script>'
    )
