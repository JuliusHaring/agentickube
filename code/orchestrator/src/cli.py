"""CLI entrypoint for Job / CronJob mode.

Reads AGENT_QUERY from the environment, runs the orchestration once, then exits.
The operator sets the container command to ``python app/cli.py`` and injects
AGENT_QUERY when spec.trigger.type is "job" or "cron".
"""

import logging.config
import sys

from logic.orchestrator import orchestrate
from config import OrchestratorCLIConfig
from shared.logging import LOGGING_CONFIG, get_logger

logging.config.dictConfig(LOGGING_CONFIG)
logger = get_logger(__name__)

cli_config = OrchestratorCLIConfig()


def main() -> int:
    query = (cli_config.agent_query or "").strip()
    if not query:
        logger.error("AGENT_QUERY environment variable is required")
        return 1

    logger.info("CLI run started: query=%s", query[:120])
    try:
        result = orchestrate(query)
    except Exception as e:
        logger.error("Orchestrator run failed: %s", e)
        print(f"Orchestrator error: {e}", file=sys.stderr)
        return 1

    logger.info("CLI run completed")
    print(result)
    return 0


if __name__ == "__main__":
    sys.exit(main())
