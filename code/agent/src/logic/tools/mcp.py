from pydantic_ai import FunctionToolset
from pydantic_ai.mcp import MCPServerSSE, MCPServerStreamableHTTP
from config import agent_config


def mcp_toolset() -> list:
    toolsets = []
    for s in agent_config.mcp_servers:
        if s.type == "sse":
            toolsets.append(MCPServerSSE(s.url))
        elif s.type == "streamable_http":
            toolsets.append(MCPServerStreamableHTTP(s.url))
    return FunctionToolset(tools=toolsets)
