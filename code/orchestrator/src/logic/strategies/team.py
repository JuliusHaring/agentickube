"""team strategy: an LLM moderator decides which agent to address next."""

from opentelemetry import trace
from pydantic_ai import Agent

from config import AgentEndpoint
from logic.agent_client import query_agent
from shared.llm import LLMConfig, get_model
from shared.logging import get_logger

logger = get_logger(__name__)

_tracer = trace.get_tracer(__name__)

_MODERATOR_INSTRUCTIONS = """\
You are a moderator coordinating a team of AI agents.
Each agent has a specialty described below. Given the user's query and the
conversation so far, decide which agent should respond next, until you decide that you have all the information you need and finish the query.

To delegate: reply with ONLY the agent name (exactly as listed), nothing else.
To finish: reply with "DONE: " followed by the actual answer to the user's query (not an agent name).
Do NOT reply "DONE: <agent name>" — that means delegate to that agent by saying just the agent name.
"""


def _agent_roster(agents: list[AgentEndpoint]) -> str:
    lines = [f"- {a.name}: {a.description or 'no description'}" for a in agents]
    return "Available agents:\n" + "\n".join(lines)


async def run_team(
    query: str,
    agents: list[AgentEndpoint],
    *,
    max_rounds: int = 10,
    llm_config: LLMConfig | None = None,
    session_id: str | None = None,
    **_,
) -> tuple[str, str | None]:
    model = get_model(llm_config)
    agent_map = {a.name: a for a in agents}
    roster = _agent_roster(agents)

    moderator = Agent(
        model=model,
        instructions=_MODERATOR_INSTRUCTIONS,
        retries=2,
    )

    transcript: list[str] = [f"User query: {query}", roster]
    effective_session_id = session_id

    with _tracer.start_as_current_span(
        "strategy team",
        attributes={
            "strategy.agent_count": len(agents),
            "strategy.max_rounds": max_rounds,
        },
    ) as span:
        for round_num in range(1, max_rounds + 1):
            prompt = "\n\n".join(transcript)
            result = await moderator.run(user_prompt=prompt)
            decision = result.output.strip()

            logger.info(
                "team round %d: moderator decided '%s'", round_num, decision[:80]
            )

            chosen = None
            if decision.upper().startswith("DONE:"):
                answer_part = decision[5:].strip()
                if answer_part in agent_map:
                    chosen = agent_map[answer_part]
                else:
                    span.set_attribute("strategy.rounds_used", round_num)
                    return (answer_part, effective_session_id)

            if chosen is None:
                chosen = agent_map.get(decision)
            if not chosen:
                transcript.append(
                    f"Moderator selected unknown agent '{decision}'. "
                    f"Valid names: {list(agent_map.keys())}"
                )
                continue

            context = "\n\n".join(transcript)
            response, agent_sid = await query_agent(
                chosen.url,
                context,
                session_id=effective_session_id,
                agent_name=chosen.name,
            )
            if agent_sid and not effective_session_id:
                effective_session_id = agent_sid
            transcript.append(f"Agent {chosen.name} responded:\n{response}")

        span.set_attribute("strategy.rounds_used", max_rounds)

    final_prompt = (
        "\n\n".join(transcript)
        + "\n\nMax rounds reached. Provide your final synthesized answer now. "
        "Reply with DONE: <answer>."
    )
    result = await moderator.run(user_prompt=final_prompt)
    answer = result.output.strip()
    if answer.upper().startswith("DONE:"):
        return (answer[5:].strip(), effective_session_id)
    return (answer, effective_session_id)
