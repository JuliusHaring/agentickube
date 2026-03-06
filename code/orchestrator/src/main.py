import logging.config
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI

from config import orchestrator_config
from shared.otel import setup_fastapi_opentelemetry
from routes import query_router
from shared.logging import LOGGING_CONFIG, get_logger

logging.config.dictConfig(LOGGING_CONFIG)
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Orchestrator startup complete")
    yield


app = FastAPI(title="Orchestrator", lifespan=lifespan)

setup_fastapi_opentelemetry(app, default_service_name="orchestrator")
app.include_router(query_router)


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=orchestrator_config.port,
        reload=orchestrator_config.reload,
        log_config=LOGGING_CONFIG,
    )
