from __future__ import annotations

import argparse
import os
import sys
import uuid

from dotenv import load_dotenv

from bookly_agent.config import mock_llm_enabled
from bookly_agent.orchestrator import Orchestrator


def main() -> None:
    load_dotenv()
    parser = argparse.ArgumentParser(description="Bookly support agent interactive CLI")
    parser.add_argument("--session", help="Session ID (auto-generated if omitted)")
    parser.add_argument(
        "--mock-llm",
        action="store_true",
        default=None,
        help="Use deterministic mock LLM (default: BOOKLY_AGENT_MOCK_LLM env)",
    )
    args = parser.parse_args()

    if args.mock_llm:
        os.environ["BOOKLY_AGENT_MOCK_LLM"] = "true"

    session_id = args.session or str(uuid.uuid4())
    orchestrator = Orchestrator()

    print("Bookly Support Agent (CLI)")
    print(f"Session: {session_id}")
    if mock_llm_enabled():
        print("Mode: mock LLM")
    print("Type 'quit' or Ctrl+C to exit.\n")

    try:
        while True:
            try:
                message = input("You: ").strip()
            except EOFError:
                print()
                break

            if not message:
                continue
            if message.lower() in {"quit", "exit"}:
                break

            response = orchestrator.handle_turn(session_id, message)
            print(f"Agent: {response.reply}")
            if response.debug:
                print(f"  [debug: intent={response.intent}, flow={response.flow}, step={response.flow_step}]")
            print()
    except KeyboardInterrupt:
        print("\nGoodbye.")
        sys.exit(0)


if __name__ == "__main__":
    main()
