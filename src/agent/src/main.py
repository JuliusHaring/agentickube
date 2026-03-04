from fastapi import FastAPI
from routes import query_router
from shared.logging import get_logger

logger = get_logger(__name__)

logger.info("Starting Agent")
app = FastAPI(name="Agent")

app.include_router(router=query_router)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", reload=True)
