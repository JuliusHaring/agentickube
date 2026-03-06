"""Sequence strategy: call agents in order, piping output forward."""

from config import AgentEndpoint
from logic.agent_client import query_agent
from shared.logging import get_logger

logger = get_logger(__name__)


async def run_sequence(
    query: str,
    agents: list[AgentEndpoint],
    *,
    session_id: str | None = None,
    **_,
) -> tuple[str, str | None]:
    previous_response = ""
    effective_session_id = session_id
    for i, agent in enumerate(agents):
        if previous_response:
            full_query = (
                f"{query}\n\n"
                f"Previous agent ({agents[i - 1].name}) response:\n"
                f"{previous_response}"
            )
        else:
            full_query = query

        logger.info("Sequence step %d/%d: calling %s", i + 1, len(agents), agent.name)
        previous_response, agent_sid = await query_agent(
            agent.url, full_query, session_id=effective_session_id
        )
        if agent_sid and not effective_session_id:
            effective_session_id = agent_sid

    return (previous_response, effective_session_id)
