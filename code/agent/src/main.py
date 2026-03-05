from fastapi import FastAPI
from routes import query_router
from setup import setup_opentelemetry

app = FastAPI(name="Agent")

# Configure OTel (Logfire) before importing routes/agent so Pydantic AI instrumentation is active
setup_opentelemetry(app)
app.include_router(router=query_router)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", reload=True)
