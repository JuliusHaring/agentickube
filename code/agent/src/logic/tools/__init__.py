"""Pydantic-ai toolsets: skill code tools + MCP servers."""

from pydantic_ai import FunctionToolset

from config import agent_config
from logic.skills import load_skill_tools
from logic.tools.mcp import mcp_toolset


def assemble_toolsets() -> list:
    toolsets = []

    # Built-in skill filtering is applied at seed time (seed_workspace_skills).
    # By the time we load tools, workspace/skills/ already has the right set.
    skill_tools = load_skill_tools()
    if skill_tools:
        toolsets.append(FunctionToolset(tools=skill_tools))

    if agent_config.mcp_servers:
        toolsets.append(mcp_toolset())

    return toolsets
