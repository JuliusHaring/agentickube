"""Pydantic-ai tools (workspace file I/O and future tool modules)."""

from agent.src.logic.tools.mcp import mcp_toolset
from logic.tools.workspace import workspace_toolset
from config import llm_config


def assemble_toolsets() -> list:
    toolsets = []
    if llm_config.workspace_dir:
        toolsets.append(workspace_toolset())
    if llm_config.mcp_servers:
        toolsets.append(mcp_toolset())
    return toolsets
