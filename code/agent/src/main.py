from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI

from logic.skills import seed_workspace_skills
from routes import query_router
from setup import setup_opentelemetry
from shared.logging import get_logger, LOGGING_CONFIG

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: seed skills into workspace before serving requests
    seed_workspace_skills()
    logger.info("Application startup complete")
    yield
    # Shutdown: nothing to clean up


app = FastAPI(title="Agent", lifespan=lifespan)

setup_opentelemetry(app)
app.include_router(query_router)


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_config=LOGGING_CONFIG,  # ✅ pass dict, not None
    )
