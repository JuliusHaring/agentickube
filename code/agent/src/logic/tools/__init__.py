"""Pydantic-ai toolsets: skill system tools + MCP servers."""

import inspect

from pydantic_ai import FunctionToolset

from config import agent_config
from logic.skills import get_skill_instructions, run_skill_script
from logic.tools.mcp import mcp_toolsets
from shared.logging import get_logger

logger = get_logger(__name__)

# Cap tool string output so the model request stays under context limits (e.g. Gemini 1M).
MAX_TOOL_OUTPUT_CHARS = 60_000


def _adapt_tool_call(fn, args: tuple, kwargs: dict) -> tuple[tuple, dict]:
    """Adapt (args, kwargs) to match fn's signature so pydantic-ai's RunContext etc. don't break no-arg tools."""
    sig = inspect.signature(fn)
    params = list(sig.parameters.values())
    n_pos = 0
    takes_var_pos = False
    param_names = set()
    for p in params:
        if p.kind == inspect.Parameter.VAR_POSITIONAL:
            takes_var_pos = True
        elif p.kind in (
            inspect.Parameter.POSITIONAL_ONLY,
            inspect.Parameter.POSITIONAL_OR_KEYWORD,
        ):
            n_pos += 1
            param_names.add(p.name)
        elif p.kind == inspect.Parameter.KEYWORD_ONLY:
            param_names.add(p.name)
        elif p.kind == inspect.Parameter.VAR_KEYWORD:
            param_names.add(None)  # accepts any kwargs
    call_args = args if takes_var_pos else args[:n_pos]
    if None in param_names:
        call_kwargs = kwargs
    else:
        call_kwargs = {k: v for k, v in kwargs.items() if k in param_names}
    return call_args, call_kwargs


def _wrap_tool_output(fn):
    """Wrap a tool so that string return values are truncated to MAX_TOOL_OUTPUT_CHARS.
    Also adapts arguments to the function's signature so pydantic-ai passing RunContext
    as first arg does not break skill tools that take no arguments (e.g. get_top_movers()).
    """

    def wrapped(*args, **kwargs):
        call_args, call_kwargs = _adapt_tool_call(fn, args, kwargs)
        logger.info(
            f"Calling tool: {fn.__name__} with args: {call_args} and kwargs: {call_kwargs}"
        )
        try:
            out = fn(*call_args, **call_kwargs)
        except Exception as e:
            logger.error(
                "Tool error: name=%s args=%s error=%s",
                getattr(fn, "__name__", "?"),
                call_kwargs if call_kwargs else (call_args if call_args else None),
                e,
            )
            return f"Tool error for tool {getattr(fn, '__name__', '?')}: {e}"
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

    skill_system_tools = [
        _wrap_tool_output(get_skill_instructions),
        _wrap_tool_output(run_skill_script),
    ]
    toolsets.append(FunctionToolset(tools=skill_system_tools))

    if agent_config.mcp_servers:
        toolsets.extend(mcp_toolsets())

    return toolsets
