"""
Autonomous Codebase Documenter
-------------------------------
Run:
    uvicorn main:app --reload --port 8000

Swagger UI: http://localhost:8000/docs
"""

from pathlib import Path
import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI

from app.connection import init_db
from app.routes import router
from fastapi.staticfiles import StaticFiles

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Creates pgvector extension + all tables if they don't exist yet
    await init_db()
    print("✅  Database ready")
    yield


app = FastAPI(
    title       = "Autonomous Codebase Documenter",
    description = (
        "Submit a GitHub repo → get module-level summaries, full project "
        "documentation, and RAG Q&A — powered by LangGraph, nomic embeddings, "
        "and pgvector."
    ),
    version  = "1.0.0",
    lifespan = lifespan,
)
BASE_DIR = Path(__file__).resolve().parent

app.mount(
    "/static",
    StaticFiles(directory=BASE_DIR / "static"),
    name="static",
)
app.include_router(router)


@app.get("/health", tags=["health"])
async def health():
    return {"status": "ok"}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)