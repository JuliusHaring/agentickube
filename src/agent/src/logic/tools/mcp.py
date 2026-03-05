from pydantic_ai import FunctionToolset
from pydantic_ai.mcp import MCPServerSSE, MCPServerStreamableHTTP
from agent.src.config import llm_config


def mcp_toolset() -> list:
    toolsets = []
    for s in llm_config.mcp_servers:
        if s.type == "sse":
            toolsets.append(MCPServerSSE(s.url))
        elif s.type == "streamable_http":
            toolsets.append(MCPServerStreamableHTTP(s.url))
    return FunctionToolset(tools=toolsets)
