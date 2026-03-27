"""
FastAPI entrypoint

Run:
    uvicorn app.main:app --reload --port 8000
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.router import api_router
from app.core.lifespan import lifespan
from app.core.settings import settings


def create_app() -> FastAPI:
    """
    Application factory.
    Keeps main clean.
    """

    app = FastAPI(
        title=settings.APP_TITLE,
        version=settings.APP_VERSION,
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:5173",
            "http://127.0.0.1:5173",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    settings.static_path.mkdir(parents=True, exist_ok=True)
    app.mount("/static", StaticFiles(directory=settings.static_path), name="static")

    app.include_router(api_router)

    @app.get("/health")
    async def health():
        return {"status": "ok"}

    return app


app = create_app()
