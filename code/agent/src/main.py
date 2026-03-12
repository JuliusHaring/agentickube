import logging.config
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI

from shared.session import clean_session_folder
from security import get_auth_dependencies, validate_auth_config
from config import agent_config
from logic.tools.skills import sync_workspace_from_repo
from routes import query_router
from shared.otel import setup_fastapi_opentelemetry
from shared.logging import LOGGING_CONFIG, get_logger  #
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import atexit


logger = get_logger(__name__)


scheduler = BackgroundScheduler()

if agent_config.session_clean_interval:
    logger.info(
        f"Adding session clean job with interval: {agent_config.session_clean_interval} and max history: {agent_config.session_max_history}"
    )
    scheduler.add_job(
        clean_session_folder,
        CronTrigger.from_crontab(agent_config.session_clean_interval),
        args=[agent_config.workspace_dir, agent_config.session_max_history],
    )


@atexit.register
def shutdown():
    scheduler.shutdown()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logging.config.dictConfig(LOGGING_CONFIG)

    validate_auth_config()
    sync_workspace_from_repo()
    scheduler.start()
    yield


app = FastAPI(title="Agent", lifespan=lifespan, dependencies=get_auth_dependencies())

setup_fastapi_opentelemetry(app, default_service_name="agent")
app.include_router(query_router)


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=agent_config.port,
        reload=agent_config.reload,
        log_config=LOGGING_CONFIG,
    )
