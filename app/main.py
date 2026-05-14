from fastapi import FastAPI
from fastapi.responses import PlainTextResponse

from app.api import admin, chat, session
from app.config.settings import get_settings
from app.dependencies import get_metrics_registry, get_registry
from app.infra.logger import configure_logging
from app.infra.middleware import RequestContextMiddleware


def create_app() -> FastAPI:
    configure_logging()
    settings = get_settings()
    app = FastAPI(title=settings.app_name, version="0.1.0")
    app.add_middleware(RequestContextMiddleware, metrics=get_metrics_registry())

    @app.get("/health")
    async def health() -> dict:
        return {"status": "ok", "service": settings.app_name}

    @app.get("/ready")
    async def readiness() -> dict:
        registry = get_registry()
        return {
            "status": "ready",
            "service": settings.app_name,
            "tools": len(registry.list_tools()),
            "context_store": "redis" if settings.redis_url.startswith(("redis://", "rediss://")) else "memory",
            "llm": "remote" if settings.llm_api_key else "local",
        }

    @app.get("/metrics", response_class=PlainTextResponse)
    async def metrics() -> str:
        return get_metrics_registry().render_prometheus()

    app.include_router(chat.router)
    app.include_router(session.router)
    app.include_router(admin.router)
    return app


app = create_app()
