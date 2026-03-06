from pydantic_ai import Agent
from pydantic_ai.messages import (
    ModelMessage,
    ModelRequest,
    ModelResponse,
    TextPart,
    UserPromptPart,
)

from logic.sessions import (
    HistoryMessage,
    load_history,
    save_history,
    extract_steps_from_run,
)
from config import agent_config
from logic.providers import get_model
from logic.prompt import instructions, skills_prompt
from logic.tools import assemble_toolsets
from shared.logging import get_logger

logger = get_logger(__name__)


def _build_agent() -> Agent:
    return Agent(
        model=get_model(),
        instructions=instructions(),
        toolsets=assemble_toolsets(),
        retries=3,
    )


def agent_loop(query: str, use_memory: bool, session_id: str | None = None) -> str:
    logger.info(
        "Agent loop started: use_memory=%s session_id=%s query=%s",
        use_memory,
        session_id,
        len(query) > 80 and query[:80] + "... [truncated]" or query,
    )
    history: list[HistoryMessage] = load_history(session_id) if use_memory else []

    try:
        skills = skills_prompt()
        logger.info(f"Skills: {skills}")

        # Build message history for the model. ModelMessage is ModelRequest | ModelResponse, not a constructor.
        def _to_model_message(m: HistoryMessage) -> ModelMessage:
            if m.role == "user":
                return ModelRequest(parts=[UserPromptPart(m.content)])
            return ModelResponse(parts=[TextPart(content=m.content)])

        message_history: list[ModelMessage] = [_to_model_message(m) for m in history]
        user_content_parts = [p for p in [skills, query] if p]
        user_prompt = "\n\n".join(user_content_parts)

        logger.info(f"History: {message_history}")

        res = _build_agent().run_sync(
            user_prompt=user_prompt,
            message_history=message_history or None,
        )
        output = res.output

        if use_memory:
            history.append(HistoryMessage(role="user", content=query))
            steps = extract_steps_from_run(res)
            history.append(
                HistoryMessage(
                    role="assistant", content=output, steps=steps if steps else None
                )
            )
            max_n = max(1, agent_config.conversation_max_history)
            if len(history) > max_n:
                history = history[-max_n:]
            save_history(session_id, history)

        return output
    except Exception as e:
        logger.error("Agent run failed: %s", e)
        return f"Agent error: {e}"
