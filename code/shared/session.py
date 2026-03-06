"""Shared session ID validation and history storage. Used by agent and orchestrator."""

from __future__ import annotations

import json
import uuid
from pathlib import Path

from pydantic import BaseModel


class HistoryMessage(BaseModel):
    role: str  # "user" | "assistant"
    content: str
    steps: list[dict] | None = None
    """Optional intermediate steps for assistant turns."""
    intermediate_messages: list[dict] | None = None
    """Serialized model messages (request/response + tool calls) for this turn, when present."""


def validate_session_id(session_id: str | None, *, memory_enabled: bool) -> str:
    """Resolve or validate session_id. Returns a UUID in 32-char hex (no hyphens).

    - If memory_enabled is False and session_id is provided, raises ValueError.
    - If session_id is missing/empty, returns a new UUID (hex).
    - Otherwise validates session_id as UUID and returns it normalized to hex.
    """
    if not memory_enabled and session_id and session_id.strip():
        raise ValueError(
            "session_id is only allowed when conversation memory is enabled"
        )
    if not memory_enabled:
        return uuid.uuid4().hex  # caller may ignore when not using memory
    if not session_id or session_id.strip() == "":
        return uuid.uuid4().hex
    try:
        return uuid.UUID(session_id.strip()).hex
    except (ValueError, TypeError, AttributeError):
        raise ValueError("session_id must be a valid UUID")


def session_dir(base_dir: str) -> Path:
    return Path(base_dir) / "sessions"


def session_path(base_dir: str, session_id: str) -> Path:
    return session_dir(base_dir) / f"{session_id}.json"


def load_history(
    base_dir: str, session_id: str, *, logger=None
) -> list[HistoryMessage]:
    path = session_path(base_dir, session_id)
    if not path.is_file():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return [HistoryMessage(**item) for item in data]
    except Exception as e:
        if logger:
            logger.warning("Failed to load session history %s: %s", session_id, e)
        return []


def save_history(base_dir: str, session_id: str, history: list[HistoryMessage]) -> None:
    path = session_path(base_dir, session_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps([m.model_dump() for m in history], indent=0, default=str),
        encoding="utf-8",
    )


def history_prompt(
    history: list[HistoryMessage], *, include_steps: bool = False
) -> str:
    if not history:
        return ""
    lines = ["# Conversation so far\n"]
    for m in history:
        if m.role == "user":
            lines.append(f"User: {m.content}")
        else:
            if include_steps and m.steps:
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
