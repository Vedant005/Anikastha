"""
PR-Sentinel Model Context Protocol (MCP) Package
Exposes PR-Sentinel tools, resources, and prompts to Cursor, Claude Desktop,
Windsurf, VS Code, JetBrains, and CLI, and connects LangGraph to external MCP servers.
"""

from app.mcp.server import mcp_server

__all__ = ["mcp_server"]
