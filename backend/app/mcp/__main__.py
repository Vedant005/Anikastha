"""
PR-Sentinel MCP Server CLI Entrypoint.
Allows running the server via: python -m app.mcp [--transport stdio|sse]
"""

import argparse
import sys

from app.mcp.server import mcp_server


def main():
    parser = argparse.ArgumentParser(description="PR-Sentinel Model Context Protocol (MCP) Server")
    parser.add_argument(
        "--transport",
        choices=["stdio", "sse"],
        default="stdio",
        help="Transport protocol to use (default: stdio)",
    )
    args = parser.parse_args()

    # Run the server on the selected transport
    try:
        mcp_server.run(transport=args.transport)
    except KeyboardInterrupt:
        sys.exit(0)


if __name__ == "__main__":
    main()
