import time
from typing import Protocol


class SessionLock(Protocol):
    async def acquire(self, session_id: str, ttl_seconds: int) -> bool:
        ...

    async def release(self, session_id: str) -> None:
        ...


class MemorySessionLock:
    def __init__(self):
        self._locks: dict[str, float] = {}

    async def acquire(self, session_id: str, ttl_seconds: int) -> bool:
        now = time.time()
        self._purge_expired(now)
        if session_id in self._locks:
            return False
        self._locks[session_id] = now + ttl_seconds
        return True

    async def release(self, session_id: str) -> None:
        self._locks.pop(session_id, None)

    def _purge_expired(self, now: float) -> None:
        expired = [session_id for session_id, expires_at in self._locks.items() if expires_at <= now]
        for session_id in expired:
            self._locks.pop(session_id, None)


class RedisSessionLock:
    def __init__(self, redis_url: str, key_prefix: str = "session-lock"):
        try:
            from redis.asyncio import Redis
        except ImportError as exc:
            raise RuntimeError("Install redis to use Redis-backed session locks") from exc

        self._client = Redis.from_url(redis_url, decode_responses=True)
        self.key_prefix = key_prefix

    async def acquire(self, session_id: str, ttl_seconds: int) -> bool:
        result = await self._client.set(self._key(session_id), "1", ex=ttl_seconds, nx=True)
        return bool(result)

    async def release(self, session_id: str) -> None:
        await self._client.delete(self._key(session_id))

    def _key(self, session_id: str) -> str:
        return f"{self.key_prefix}:{session_id}"
