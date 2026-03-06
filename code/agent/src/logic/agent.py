from pydantic_ai import Agent

from logic.history import get_history, history_to_model_messages, record_turn
from logic.sessions import extract_steps_from_run
from config import agent_config
from logic.providers import get_model
from logic.prompt import agent_instructions, skills_prompt
from logic.tools import assemble_toolsets
from shared.logging import get_logger

logger = get_logger(__name__)


def _build_agent() -> Agent:
    return Agent(
        model=get_model(),
        instructions=agent_instructions(),
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
    history = get_history(session_id, use_memory)

    try:
        skills = skills_prompt()
        logger.info("Skills loaded for context (not in user prompt)")

        message_history = history_to_model_messages(history)
        res = _build_agent().run_sync(
            user_prompt=query,
            message_history=message_history or None,
            instructions=skills if skills else None,
        )
        output = res.output

        if use_memory and session_id:
            steps = extract_steps_from_run(res)
            try:
                new_messages = list(res.new_messages())
            except Exception:
                new_messages = None
            record_turn(
                session_id,
                history,
                query,
                output,
                steps if steps else None,
                max(1, agent_config.conversation_max_history),
                new_messages=new_messages,
            )

        return output
    except Exception as e:
        logger.error("Agent run failed: %s", e)
        raise e
