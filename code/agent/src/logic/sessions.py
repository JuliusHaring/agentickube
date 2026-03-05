import json
import uuid
from pathlib import Path

from fastapi import HTTPException
from pydantic import BaseModel

from config import agent_config
from shared.logging import get_logger

logger = get_logger(__name__)


def extract_steps_from_run(result) -> list[dict]:
    """Build list of {tool, args, result} from the run's new messages (tool calls + returns)."""
    steps: list[dict] = []
    try:
        messages = result.new_messages()
    except Exception:
        return steps
    pending_calls: list[tuple[str, dict]] = []  # (tool_name, args)
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


def get_session_id(session_id: str | None) -> str | None:
    """Get session_id for API use. Raises HTTPException 400 if invalid.

    - session_id is only allowed when conversation memory is enabled.
    - When provided, session_id must be a valid UUID.
    - If not provided, generate a new session_id.
    """
    if not agent_config.conversation_memory_enabled:
        raise HTTPException(
            status_code=400,
            detail="session_id is only allowed when conversation memory is enabled (spec.conversation.enabled)",
        )
    if not session_id or session_id.strip() == "":
        return uuid.uuid4().hex
    try:
        return str(uuid.UUID(session_id.strip()))
    except (ValueError, TypeError, AttributeError):
        raise HTTPException(
            status_code=400,
            detail="session_id must be a valid UUID",
        )


class HistoryMessage(BaseModel):
    role: str  # "user" | "assistant"
    content: str
    steps: list[dict] | None = None
    """Optional intermediate steps for assistant turns: list of {"tool": str, "args": dict, "result": str}."""


def session_dir() -> Path:
    return Path(agent_config.workspace_dir) / "sessions"


def session_path(session_id: str) -> Path | None:
    sid = get_session_id(session_id)
    return session_dir() / f"{sid}.json" if sid else None


def load_history(session_id: str) -> list[HistoryMessage]:
    path = session_path(session_id)
    if not path or not path.is_file():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return [HistoryMessage(**item) for item in data]
    except Exception as e:
        logger.warning("Failed to load session history %s: %s", session_id, e)
        return []


def save_history(session_id: str, history: list[HistoryMessage]) -> None:
    path = session_path(session_id)
    if not path:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps([m.model_dump() for m in history], indent=0),
        encoding="utf-8",
    )


def history_prompt(history: list[HistoryMessage]) -> str:
    if not history:
        return ""
    lines = ["# Conversation so far\n"]
    for m in history:
        if m.role == "user":
            lines.append(f"User: {m.content}")
        else:
            if m.steps:
                for s in m.steps:
                    tool = s.get("tool", "?")
                    args = s.get("args") or {}
                    result = s.get("result", "")
                    args_str = ", ".join(f"{k}={v!r}" for k, v in args.items())
                    lines.append(
                        f"  [tool] {tool}({args_str}) -> {result[:200]}{'...' if len(result) > 200 else ''}"
                    )
            lines.append(f"Assistant: {m.content}")
    return "\n".join(lines)
