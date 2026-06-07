from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .core.config import settings
from .core.logging import setup_logging
from .api.routes import chat as chat_route
from .api.routes import health as health_route


def create_app() -> FastAPI:
    setup_logging()
    app = FastAPI(title="basic-agent", version="0.1.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health_route.router, prefix="/api")
    app.include_router(chat_route.router, prefix="/api")
    return app


app = create_app()
