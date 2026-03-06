"""Pydantic-ai toolsets: skill code tools + MCP servers."""

from pydantic_ai import FunctionToolset

from config import agent_config
from logic.skills import load_skill_tools
from logic.tools.mcp import mcp_toolsets


def assemble_toolsets() -> list:
    toolsets = []

    skill_tools = load_skill_tools()
    if skill_tools:
        toolsets.append(FunctionToolset(tools=skill_tools))

    if agent_config.mcp_servers:
        toolsets.extend(mcp_toolsets())

    return toolsets
