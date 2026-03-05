from fastapi import FastAPI
import uvicorn

from logic.skills import seed_workspace_skills
from routes import query_router
from setup import setup_opentelemetry
from shared.logging import get_logger, LOGGING_CONFIG

logger = get_logger(__name__)

# Seed operator-provided skills (bootstrap volume) into workspace before serving requests.
seed_workspace_skills()

app = FastAPI(title="Agent")

setup_opentelemetry(app)
app.include_router(query_router)


@app.on_event("startup")
async def startup_event():
    logger.info("Application startup complete")


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_config=LOGGING_CONFIG,  # ✅ pass dict, not None
    )
