import logging.config
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI

from config import agent_config
from logic.skills import seed_workspace_skills
from routes import query_router
from logic.otel import setup_fastapi_opentelemetry
from shared.logging import LOGGING_CONFIG, get_logger

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logging.config.dictConfig(LOGGING_CONFIG)

    seed_workspace_skills()
    yield


app = FastAPI(title="Agent", lifespan=lifespan)

setup_fastapi_opentelemetry(app)
app.include_router(query_router)


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=agent_config.port,
        reload=agent_config.reload,
        log_config=LOGGING_CONFIG,
    )
