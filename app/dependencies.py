from functools import lru_cache

from app.agent.executor import ReActExecutor
from app.config.settings import get_settings
from app.context.manager import ContextManager
from app.context.session_lock import MemorySessionLock, RedisSessionLock, SessionLock
from app.context.store import RedisContextStore
from app.llm.client import HeuristicLLMClient, OpenAICompatibleLLMClient
from app.llm.retry import CircuitBreaker
from app.tools import ToolRegistry, build_default_registry


@lru_cache
def get_registry() -> ToolRegistry:
    settings = get_settings()
    return build_default_registry(timeout_seconds=settings.tool_timeout_seconds)


@lru_cache
def get_context_manager() -> ContextManager:
    settings = get_settings()
    store = None
    if settings.redis_url.startswith("redis://") or settings.redis_url.startswith("rediss://"):
        store = RedisContextStore(settings.redis_url)
    return ContextManager(
        max_tokens=settings.context_max_tokens,
        keep_recent=settings.context_keep_recent,
        ttl_seconds=settings.context_ttl_seconds,
        store=store,
    )


@lru_cache
def get_session_lock() -> SessionLock:
    settings = get_settings()
    if settings.redis_url.startswith("redis://") or settings.redis_url.startswith("rediss://"):
        return RedisSessionLock(settings.redis_url)
    return MemorySessionLock()


@lru_cache
def get_llm_client():
    settings = get_settings()
    if settings.llm_api_key:
        return OpenAICompatibleLLMClient(
            base_url=settings.llm_base_url,
            api_key=settings.llm_api_key,
            model=settings.llm_model,
            timeout=settings.llm_timeout,
            max_retries=settings.llm_max_retries,
            circuit_breaker=CircuitBreaker(
                failure_threshold=settings.llm_circuit_failure_threshold,
                recovery_seconds=settings.llm_circuit_recovery_seconds,
            ),
        )
    return HeuristicLLMClient()


@lru_cache
def get_executor() -> ReActExecutor:
    settings = get_settings()
    return ReActExecutor(
        llm=get_llm_client(),
        registry=get_registry(),
        ctx=get_context_manager(),
        max_steps=settings.agent_max_steps,
    )
