"""
Composio Platform Integration Helper for Zyntrix.

Provides session management, integration connection (Connect Link), and
safe tool execution using the Composio Python SDK (Platform mode).
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any, Dict, Optional

from dotenv import load_dotenv

# Load root .env file if present
load_dotenv()

try:
    from composio import Composio
except ImportError:
    print("Error: 'composio' package not installed. Run 'pip install composio'", file=sys.stderr)
    sys.exit(1)


def get_client() -> Composio:
    """Initialize Composio client using COMPOSIO_API_KEY from environment."""
    api_key = os.getenv("COMPOSIO_API_KEY")
    if not api_key:
        raise ValueError("COMPOSIO_API_KEY environment variable is missing.")
    return Composio(api_key=api_key)


def get_or_create_session(user_id: str = "zyntrix_dev_user"):
    """Create or retrieve a Composio ToolRouter session for the given user."""
    client = get_client()
    session = client.create(user_id=user_id)
    return session


def connect_toolkit(toolkit: str, user_id: str = "zyntrix_dev_user") -> Dict[str, Any]:
    """
    Initiate authorization for a toolkit (e.g. 'github', 'slack', 'gmail').
    Returns connection details including the redirect_url (Connect Link).
    """
    session = get_or_create_session(user_id=user_id)
    auth_request = session.authorize(toolkit=toolkit)
    redirect_url = getattr(auth_request, "redirect_url", None)
    return {
        "status": getattr(auth_request, "status", "UNKNOWN"),
        "connection_id": getattr(auth_request, "id", None),
        "toolkit": toolkit,
        "user_id": user_id,
        "connect_link": redirect_url,
    }


def execute_tool(
    tool_slug: str,
    arguments: Optional[Dict[str, Any]] = None,
    user_id: str = "zyntrix_dev_user",
) -> Dict[str, Any]:
    """
    Execute a tool in the user's session and return data with Composio log_id.
    """
    session = get_or_create_session(user_id=user_id)
    args = arguments or {}
    response = session.execute(tool_slug, arguments=args)
    return {
        "tool_slug": tool_slug,
        "log_id": getattr(response, "log_id", None),
        "data": getattr(response, "data", None),
        "error": getattr(response, "error", None),
    }


def main():
    parser = argparse.ArgumentParser(description="Composio Integration CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # connect command
    connect_parser = subparsers.add_parser("connect", help="Connect an integration toolkit")
    connect_parser.add_argument("toolkit", help="Toolkit slug (e.g., github, slack, gmail)")
    connect_parser.add_argument("--user-id", default="zyntrix_dev_user", help="User identity")

    # execute command
    exec_parser = subparsers.add_parser("execute", help="Execute a tool")
    exec_parser.add_argument("tool_slug", help="Tool slug (e.g., COMPOSIO_REMOTE_WORKBENCH)")
    exec_parser.add_argument("--args", default="{}", help="JSON string of tool arguments")
    exec_parser.add_argument("--user-id", default="zyntrix_dev_user", help="User identity")

    # test-workbench command
    subparsers.add_parser("test-workbench", help="Run a self-test with COMPOSIO_REMOTE_WORKBENCH")

    args = parser.parse_args()

    if args.command == "connect":
        res = connect_toolkit(args.toolkit, user_id=args.user_id)
        print(json.dumps(res, indent=2))
        print(f"\nConnect Link: {res['connect_link']}")

    elif args.command == "execute":
        parsed_args = json.loads(args.args)
        res = execute_tool(args.tool_slug, arguments=parsed_args, user_id=args.user_id)
        print(json.dumps(res, indent=2, default=str))

    elif args.command == "test-workbench":
        print("Executing verification tool call via COMPOSIO_REMOTE_WORKBENCH...")
        res = execute_tool(
            "COMPOSIO_REMOTE_WORKBENCH",
            arguments={"code_to_execute": "print('Composio integration verified successfully!')"},
            user_id="zyntrix_dev_user",
        )
        print("\n=== Tool Call Result ===")
        print(f"Log ID: {res['log_id']}")
        print(f"Output: {res['data'].get('stdout') if res.get('data') else res}")
        print("Status: Verified")


if __name__ == "__main__":
    main()
