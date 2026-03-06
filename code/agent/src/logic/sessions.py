"""Session and history for the agent. Uses shared.session for storage and validation."""

from pathlib import Path

from fastapi import HTTPException

from config import agent_config
from shared.session import (
    HistoryMessage,
    history_prompt as _history_prompt_shared,
    load_history as _load_history_shared,
    save_history as _save_history_shared,
    validate_session_id as _validate_session_id,
)
from shared.logging import get_logger

logger = get_logger(__name__)


def get_session_id(session_id: str | None) -> str | None:
    """Resolve session_id for API use. Raises HTTPException 400 if invalid."""
    try:
        return _validate_session_id(
            session_id, memory_enabled=agent_config.conversation_memory_enabled
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


def session_dir() -> Path:
    return Path(agent_config.workspace_dir) / "sessions"


def session_path(session_id: str) -> Path | None:
    sid = get_session_id(session_id)
    return session_dir() / f"{sid}.json" if sid else None


def load_history(session_id: str) -> list[HistoryMessage]:
    return _load_history_shared(agent_config.workspace_dir, session_id, logger=logger)


def save_history(session_id: str, history: list[HistoryMessage]) -> None:
    _save_history_shared(agent_config.workspace_dir, session_id, history)


def history_prompt(history: list[HistoryMessage]) -> str:
    return _history_prompt_shared(history, include_steps=True)


def extract_steps_from_run(result) -> list[dict]:
    """Build list of {tool, args, result} from the run's new messages (tool calls + returns)."""
    steps: list[dict] = []
    try:
        messages = result.new_messages()
    except Exception:
        return steps
    pending_calls: list[tuple[str, dict]] = []
    for msg in messages:
        parts = getattr(msg, "parts", None) or []
        for part in parts:
            part_type = type(part).__name__
            if "ToolCall" in part_type or "tool_call" in str(
                getattr(part, "part_kind", "")
            ):
                name = getattr(part, "tool_name", None) or "?"
                args = getattr(part, "args", None)
                if args is not None and not isinstance(args, dict):
                    args = dict(args) if hasattr(args, "items") else {}
                pending_calls.append((name, args or {}))
            elif "ToolReturn" in part_type or "tool_return" in str(
                getattr(part, "part_kind", "")
            ):
                content = getattr(part, "content", None)
                result_str = str(content) if content is not None else ""
                if pending_calls:
                    tool_name, tool_args = pending_calls.pop(0)
                    steps.append(
                        {"tool": tool_name, "args": tool_args, "result": result_str}
                    )
    return steps
