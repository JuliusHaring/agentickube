import logging.config
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI

from security import get_auth_dependencies, validate_auth_config
from config import agent_config
from logic.skills import sync_workspace_from_repo
from routes import query_router
from shared.otel import setup_fastapi_opentelemetry
from shared.logging import LOGGING_CONFIG, get_logger

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logging.config.dictConfig(LOGGING_CONFIG)

    validate_auth_config()
    sync_workspace_from_repo()
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
