"""Strategy dispatcher -- used by both HTTP and CLI entrypoints."""

import asyncio

from opentelemetry import trace

from config import orchestrator_config
from logic.strategies import STRATEGY_MAP
from shared.llm import LLMConfig
from shared.logging import get_logger

logger = get_logger(__name__)

_tracer = trace.get_tracer(__name__)


def orchestrate(
    query: str,
    session_id: str | None = None,
) -> tuple[str, str | None]:
    cfg = orchestrator_config
    strategy_name = cfg.strategy.strip().lower()
    strategy_fn = STRATEGY_MAP.get(strategy_name)

    if strategy_fn is None:
        raise ValueError(
            f"Unknown strategy '{strategy_name}'. "
            f"Available: {list(STRATEGY_MAP.keys())}"
        )

    if not cfg.agents:
        raise ValueError("No agents configured for orchestrator")

    logger.info(
        "Running strategy=%s agents=%s session_id=%s query=%s",
        strategy_name,
        [a.name for a in cfg.agents],
        session_id,
        query[:80],
    )

    try:
        llm_config = LLMConfig()
    except Exception:
        llm_config = None

    with _tracer.start_as_current_span(
        "orchestrate",
        attributes={
            "orchestrator.name": cfg.orchestrator_name or "",
            "orchestrator.strategy": strategy_name,
            "orchestrator.agents": [a.name for a in cfg.agents],
        },
    ):
        result, effective_session_id = asyncio.run(
            strategy_fn(
                query=query,
                agents=cfg.agents,
                max_rounds=cfg.max_rounds,
                llm_config=llm_config,
                session_id=session_id,
            )
        )
    return (result, effective_session_id)
