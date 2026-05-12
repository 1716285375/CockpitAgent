from fastapi import FastAPI

from app.api import admin, chat, session
from app.config.settings import get_settings
from app.infra.logger import configure_logging


def create_app() -> FastAPI:
    configure_logging()
    settings = get_settings()
    app = FastAPI(title=settings.app_name, version="0.1.0")

    @app.get("/health")
    async def health() -> dict:
        return {"status": "ok", "service": settings.app_name}

    app.include_router(chat.router)
    app.include_router(session.router)
    app.include_router(admin.router)
    return app


app = create_app()

