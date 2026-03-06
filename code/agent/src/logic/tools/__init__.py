"""Pydantic-ai toolsets: skill code tools + MCP servers."""

from pydantic_ai import FunctionToolset

from config import agent_config
from logic.skills import load_skill_tools
from logic.tools.mcp import mcp_toolsets

# Cap tool string output so the model request stays under context limits (e.g. Gemini 1M).
MAX_TOOL_OUTPUT_CHARS = 60_000


def _wrap_tool_output(fn):
    """Wrap a tool so that string return values are truncated to MAX_TOOL_OUTPUT_CHARS."""

    def wrapped(*args, **kwargs):
        out = fn(*args, **kwargs)
        if isinstance(out, str) and len(out) > MAX_TOOL_OUTPUT_CHARS:
            return (
                out[:MAX_TOOL_OUTPUT_CHARS]
                + f"\n\n[Output truncated: was {len(out)} chars total.]"
            )
        return out

    wrapped.__name__ = getattr(fn, "__name__", "tool")
    wrapped.__doc__ = getattr(fn, "__doc__", None)
    return wrapped


def assemble_toolsets() -> list:
    toolsets = []

    skill_tools = [_wrap_tool_output(t) for t in load_skill_tools()]
    if skill_tools:
        toolsets.append(FunctionToolset(tools=skill_tools))

    if agent_config.mcp_servers:
        toolsets.extend(mcp_toolsets())

    return toolsets
