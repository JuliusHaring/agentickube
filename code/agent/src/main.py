import logging.config
import os
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI

from logic.skills import seed_workspace_skills
from routes import query_router
from logic.otel import setup_opentelemetry
from shared.logging import LOGGING_CONFIG, get_logger

logging.config.dictConfig(LOGGING_CONFIG)
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    seed_workspace_skills()
    logger.info("Application startup complete")
    yield


app = FastAPI(title="Agent", lifespan=lifespan)

setup_opentelemetry(app)
app.include_router(query_router)


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.environ.get("PORT", "8000")),
        reload=os.environ.get("RELOAD", "").lower() == "true",
        log_config=LOGGING_CONFIG,
    )
