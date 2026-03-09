from opentelemetry import trace
from pydantic_ai import Agent
from pydantic_ai.exceptions import UnexpectedModelBehavior

from logic.history import get_history, history_to_model_messages, record_turn
from logic.session import extract_steps_from_run
from config import agent_config
from logic.providers import get_model
from logic.prompt import agent_instructions, skills_prompt
from logic.tools import assemble_toolsets
from shared.logging import get_logger

logger = get_logger(__name__)
_tracer = trace.get_tracer(__name__)


def _build_agent() -> Agent:
    return Agent(
        model=get_model(),
        instructions=agent_instructions(),
        toolsets=assemble_toolsets(),
        retries=3,
    )


def agent_loop(query: str, session_id: str | None = None) -> str:
    logger.info(
        "Agent loop started: session_id=%s query=%s",
        session_id,
        len(query) > 80 and query[:80] + "... [truncated]" or query,
    )
    history = get_history(session_id)

    attrs: dict[str, str | int] = {}
    if session_id:
        attrs["session.id"] = session_id

    try:
        skills = skills_prompt()
        logger.info("Skills loaded for context (not in user prompt)")

        message_history = history_to_model_messages(history)
        with _tracer.start_as_current_span("agent_run", attributes=attrs) as span:
            res = _build_agent().run_sync(
                user_prompt=query,
                message_history=message_history or None,
                instructions=skills if skills else None,
            )
            try:
                usage = res.usage()
            except Exception:
                usage = None
            if usage is not None:
                inp = getattr(usage, "input_tokens", None)
                out = getattr(usage, "output_tokens", None)
                if inp is not None:
                    span.set_attribute("gen_ai.usage.input_tokens", inp)
                if out is not None:
                    span.set_attribute("gen_ai.usage.output_tokens", out)

        output = res.output

        # TODO: res.result? because res is an AgentRunResult[str] not ModelResponse
        steps = extract_steps_from_run(res)
        if agent_config.conversation_memory_enabled and session_id:
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
                agent_config.conversation_max_history,
                new_messages=new_messages,
            )

        return output
    except UnexpectedModelBehavior as e:
        logger.error(
            "Agent run failed (model retries exceeded): %s — often output validation (model didn't return valid str) or invalid tool calls",
            e,
        )
        raise
    except Exception as e:
        logger.error("Agent run failed: %s", e)
        raise
