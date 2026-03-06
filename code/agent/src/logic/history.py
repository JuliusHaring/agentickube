"""Session history: load/save, render for the model, and record turns."""

from pydantic_ai.messages import (
    ModelMessage,
    ModelMessagesTypeAdapter,
    ModelRequest,
    ModelResponse,
    TextPart,
    UserPromptPart,
)

from logic.sessions import HistoryMessage, load_history, save_history


def get_history(session_id: str | None, use_memory: bool) -> list[HistoryMessage]:
    """Return loaded history when use_memory and session_id are set, otherwise []."""
    if use_memory and session_id:
        return load_history(session_id)
    return []


def history_to_model_messages(history: list[HistoryMessage]) -> list[ModelMessage]:
    """Convert session history to the message format expected by the agent run.

    We only send user and assistant text (m.content), not full intermediate_messages
    (tool calls and tool results). Replaying full tool results (e.g. entire HTML pages)
    would blow input tokens and hit model limits (400) or quota (429).
    """
    result: list[ModelMessage] = []
    for m in history:
        if m.role == "user":
            result.append(ModelRequest(parts=[UserPromptPart(m.content)]))
        else:
            result.append(ModelResponse(parts=[TextPart(content=m.content)]))
    return result


def record_turn(
    session_id: str,
    history: list[HistoryMessage],
    query: str,
    output: str,
    steps: list[dict] | None,
    max_messages: int,
    new_messages: list[ModelMessage] | None = None,
) -> None:
    """Append user and assistant messages (with optional intermediate messages), trim, and save."""
    history.append(HistoryMessage(role="user", content=query))
    intermediate: list[dict] | None = None
    if new_messages:
        intermediate = ModelMessagesTypeAdapter.dump_python(new_messages)
    history.append(
        HistoryMessage(
            role="assistant",
            content=output,
            steps=steps,
            intermediate_messages=intermediate,
        )
    )
    if len(history) > max_messages:
        trimmed = history[-max_messages:]
        history.clear()
        history.extend(trimmed)
    save_history(session_id, history)
