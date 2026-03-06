"""Sequence strategy: call agents in order, piping output forward."""

from opentelemetry import trace

from config import AgentEndpoint
from logic.agent_client import query_agent
from shared.logging import get_logger

logger = get_logger(__name__)

_tracer = trace.get_tracer(__name__)


async def run_sequence(
    query: str,
    agents: list[AgentEndpoint],
    *,
    session_id: str | None = None,
    **_,
) -> tuple[str, str | None]:
    previous_response = ""
    effective_session_id = session_id
    with _tracer.start_as_current_span(
        "strategy sequence",
        attributes={"strategy.agent_count": len(agents)},
    ):
        for i, agent in enumerate(agents):
            if previous_response:
                prev_name = agents[i - 1].name
                full_query = (
                    "-----------\n"
                    f"OUTPUT FROM PREVIOUS STEP (agent: {prev_name}):\n"
                    "-----------\n"
                    f"{previous_response}"
                    "-----------\n"
                    "USER REQUEST:\n"
                    "-----------\n"
                    f"{query}\n\n"
                )
            else:
                full_query = query

            logger.info(
                "Sequence step %d/%d: calling %s", i + 1, len(agents), agent.name
            )
            previous_response, agent_sid = await query_agent(
                agent.url,
                full_query,
                session_id=effective_session_id,
                agent_name=agent.name,
            )
            if agent_sid and not effective_session_id:
                effective_session_id = agent_sid

    return (previous_response, effective_session_id)
