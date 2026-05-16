import asyncio
from contextlib import asynccontextmanager
from contextlib import suppress

from fastapi import FastAPI
from fastapi.responses import PlainTextResponse

from app.api import admin, chat, session
from app.config.nacos_client import NacosConfigClient
from app.config.runtime import apply_runtime_config
from app.config.settings import get_settings
from app.dependencies import get_metrics_registry, get_registry
from app.dependencies import get_executor
from app.infra.logger import configure_logging
from app.infra.middleware import RequestContextMiddleware


def build_lifespan(settings):
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        task = None
        if settings.nacos_server:
            client = NacosConfigClient(
                settings.nacos_server,
                settings.nacos_data_id,
                group=settings.nacos_group,
                namespace=settings.nacos_namespace,
            )

            async def on_change(payload: dict) -> None:
                apply_runtime_config(payload, executor=get_executor(), registry=get_registry())

            task = asyncio.create_task(
                client.watch_config(on_change, poll_interval_seconds=settings.nacos_poll_interval_seconds)
            )
            app.state.nacos_task = task
        try:
            yield
        finally:
            if task is not None:
                task.cancel()
                with suppress(asyncio.CancelledError):
                    await task

    return lifespan


def create_app() -> FastAPI:
    configure_logging()
    settings = get_settings()
    settings.validate_runtime()
    app = FastAPI(title=settings.app_name, version="0.1.0", lifespan=build_lifespan(settings))
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
            "enabled_tools": len(registry.list_schemas()),
            "context_store": "redis" if settings.redis_url.startswith(("redis://", "rediss://")) else "memory",
            "llm": "remote" if settings.llm_api_key else "local",
            "registry": registry.describe_runtime(),
        }

    @app.get("/metrics", response_class=PlainTextResponse)
    async def metrics() -> str:
        return get_metrics_registry().render_prometheus()

    app.include_router(chat.router)
    app.include_router(session.router)
    app.include_router(admin.router)
    return app


app = create_app()
