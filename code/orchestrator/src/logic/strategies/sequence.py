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
    # Only call agents that have a non-empty URL (operator must set ORCHESTRATOR_AGENT_*_URL)
    callable_agents = [a for a in agents if (a.url or "").strip()]
    if len(callable_agents) < len(agents):
        logger.warning(
            "Skipping %d agent(s) with empty URL; sequence will run with %d step(s)",
            len(agents) - len(callable_agents),
            len(callable_agents),
        )
    if not callable_agents:
        raise ValueError(
            "Sequence has no agents with a valid URL. "
            "Set ORCHESTRATOR_AGENT_1_URL, ORCHESTRATOR_AGENT_2_URL, ... in the orchestrator deployment."
        )
    if len(callable_agents) <= 1:
        logger.warning(
            "Sequence strategy has %d agent(s); pipeline needs multiple steps to chain (check ORCHESTRATOR_AGENT_* env vars)",
            len(callable_agents),
        )
    agents = callable_agents

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
                    f"{previous_response}\n"
                    "-----------\n"
                    "USER REQUEST:\n"
                    "-----------\n"
                    f"{query}\n\n"
                )
            else:
                full_query = query

            logger.info(
                "Sequence step %d/%d: calling %s at %s",
                i + 1,
                len(agents),
                agent.name,
                agent.url,
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
