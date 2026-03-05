"""Pydantic-ai toolsets: skill code tools + MCP servers."""

from pydantic_ai import FunctionToolset

from config import agent_config
from logic.skills import load_skill_tools
from logic.tools.mcp import mcp_toolset


def assemble_toolsets() -> list:
    toolsets = []

    builtin_filter = None
    if agent_config.skills_builtins is not None:
        raw = agent_config.skills_builtins.strip()
        builtin_filter = [s.strip() for s in raw.split(",") if s.strip()] if raw else []

    skill_tools = load_skill_tools(builtin_filter=builtin_filter)
    if skill_tools:
        toolsets.append(FunctionToolset(tools=skill_tools))

    if agent_config.mcp_servers:
        toolsets.append(mcp_toolset())

    return toolsets
