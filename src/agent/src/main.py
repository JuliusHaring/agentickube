from fastapi import FastAPI
from routes import query_router

app = FastAPI(name="Agent")

app.include_router(router=query_router)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", reload=True)
