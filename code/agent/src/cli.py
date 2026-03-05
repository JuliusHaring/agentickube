"""CLI entrypoint for Job / CronJob mode.

Reads AGENT_QUERY from the environment, runs agent_loop() once, then exits.
The operator sets the container command to ``python app/cli.py`` and injects
AGENT_QUERY when spec.trigger.type is "job" or "cron".
"""

import logging.config
import sys

from logic.skills import seed_workspace_skills
from logic.agent import agent_loop
from config import AgentCLIConfig
from shared.logging import LOGGING_CONFIG, get_logger
from logic.otel import setup_cli_opentelemetry

logging.config.dictConfig(LOGGING_CONFIG)
logger = get_logger(__name__)

agent_cli_config = AgentCLIConfig()


def main() -> int:
    query = (agent_cli_config.agent_query or "").strip()
    if not query:
        logger.error("AGENT_QUERY environment variable is required")
        return 1

    seed_workspace_skills()
    setup_cli_opentelemetry()

    logger.info("CLI run started: query=%s", query[:120])
    result = agent_loop(
        query=query,
        use_memory=agent_cli_config.conversation_memory_enabled,
    )

    if result.startswith("Agent error:"):
        logger.error("CLI run failed: %s", result)
        print(result, file=sys.stderr)
        return 1

    logger.info("CLI run completed")
    print(result)

    try:
        from opentelemetry import trace

        provider = trace.get_tracer_provider()
        if hasattr(provider, "force_flush"):
            provider.force_flush(timeout_millis=5000)
    except Exception:
        pass

    return 0


if __name__ == "__main__":
    sys.exit(main())
