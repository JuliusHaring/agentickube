from pydantic_ai import Agent

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


def agent_loop(query: str) -> str:
    logger.info(f"Agent loop started: {query}")
    try:
        skills = skills_prompt()
        full_query = f"{skills}\n\n{query}" if skills else query
        res = _build_agent().run_sync(user_prompt=full_query)
    except Exception as e:
        logger.error(f"Agent run failed: {e}")
        return f"Agent error: {e}"
    return res.output
