from pydantic_ai.mcp import MCPServerSSE, MCPServerStreamableHTTP
from config import agent_config


def mcp_toolsets() -> list:
    """Return MCP server toolsets. Each MCPServer* is already a Toolset."""
    toolsets = []
    for s in agent_config.mcp_servers:
        if s.type == "sse":
            toolsets.append(MCPServerSSE(s.url))
        elif s.type == "streamable_http":
            toolsets.append(MCPServerStreamableHTTP(s.url))
    return toolsets
