#!/usr/bin/env python3
"""
CLI Interface for Aster & Row Support Agent.
Supports interactive mode, single-shot queries, debug traces, and evaluation suite execution.

Usage:
    python3 cli.py                       # Interactive chat mode
    python3 cli.py --query "Where is ORD-1007?"  # Single-shot query
    python3 cli.py --debug               # Interactive mode with full observability traces
    python3 cli.py --eval                # Run the evaluation suite
"""

import sys
import os
import argparse
import json

# Ensure workspace root is in path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.agent.core import SupportAgent
from backend.evaluation.evaluator import EvaluationRunner

def print_banner():
    banner = r"""
  =============================================================
     Aster & Row - Reliable AI Customer Support Agent (CLI)
  =============================================================
  Type your question or order inquiry below.
  Commands:
    'exit' or 'quit' : End the conversation
    'clear'          : Reset the conversation session
    'debug on/off'   : Toggle detailed observability traces
  =============================================================
    """
    print(banner)

def format_agent_output(result: dict, show_debug: bool = False):
    print("\n" + "─" * 60)
    print("🤖 AGENT RESPONSE:")
    print("─" * 60)
    print(result.get("answer", ""))

    # Sources
    sources = result.get("sources", [])
    if sources:
        print("\n📚 SOURCES / CITATIONS:")
        for s in sources:
            print(f"   • {s.get('ref')} ({s.get('heading', '')})")

    # Handoff Recommendation
    if result.get("handoff_recommended"):
        print("\n⚠️  [HUMAN HANDOFF RECOMMENDED]")
        print(f"   Reason: {result.get('handoff_reason', 'Escalation required')}")

    # Tool Calls
    tool_calls = result.get("tool_calls", [])
    if tool_calls:
        print("\n🔧 TOOL EXECUTION:")
        for tc in tool_calls:
            print(f"   • {tc.get('tool')}({tc.get('input')}): status={tc.get('result', {}).get('status')}")

    # Debug Trace
    if show_debug and "debug_trace" in result:
        print("\n🔍 OBSERVABILITY DEBUG TRACE:")
        print(json.dumps(result["debug_trace"], indent=2))

    print("─" * 60 + "\n")

def main():
    parser = argparse.ArgumentParser(description="Aster & Row Support Agent CLI")
    parser.add_argument("--query", "-q", type=str, help="Single query to ask the agent")
    parser.add_argument("--session", "-s", type=str, default="cli-session-1", help="Session ID for tracking history")
    parser.add_argument("--debug", "-d", action="store_true", help="Enable debug observability logs")
    parser.add_argument("--eval", "-e", action="store_true", help="Run the automated evaluation suite")
    args = parser.parse_args()

    if args.eval:
        runner = EvaluationRunner()
        report = runner.run_all()
        print(f"\nRan {report['total_cases']} cases. Overall Score: {report['total_passed']}/{report['total_cases']} ({report['overall_accuracy']}%)")
        sys.exit(0 if report["overall_accuracy"] == 100.0 else 1)

    agent = SupportAgent()

    if args.query:
        result = agent.process_query(args.query, session_id=args.session)
        format_agent_output(result, show_debug=args.debug)
        return

    print_banner()
    debug_mode = args.debug
    session_id = args.session

    while True:
        try:
            user_input = input("Customer > ").strip()
            if not user_input:
                continue

            if user_input.lower() in ["exit", "quit", "q"]:
                print("\nThank you for chatting with Aster & Row. Goodbye!\n")
                break

            if user_input.lower() == "clear":
                agent.clear_session(session_id)
                print("\n[Session history cleared]\n")
                continue

            if user_input.lower() == "debug on":
                debug_mode = True
                print("\n[Debug observability mode ENABLED]\n")
                continue
            elif user_input.lower() == "debug off":
                debug_mode = False
                print("\n[Debug observability mode DISABLED]\n")
                continue

            result = agent.process_query(user_input, session_id=session_id)
            format_agent_output(result, show_debug=debug_mode)

        except (KeyboardInterrupt, EOFError):
            print("\n\nExiting. Goodbye!\n")
            break

if __name__ == "__main__":
    main()
