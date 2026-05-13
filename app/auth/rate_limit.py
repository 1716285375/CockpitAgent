import time
from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class RateLimitResult:
    allowed: bool
    remaining: int
    reset_seconds: int


class RateLimiter(Protocol):
    async def check(self, key: str, limit: int, window_seconds: int) -> RateLimitResult:
        ...


class MemoryRateLimiter:
    def __init__(self):
        self._windows: dict[str, tuple[int, float]] = {}

    async def check(self, key: str, limit: int, window_seconds: int) -> RateLimitResult:
        now = time.time()
        count, reset_at = self._windows.get(key, (0, now + window_seconds))
        if reset_at <= now:
            count = 0
            reset_at = now + window_seconds
        count += 1
        self._windows[key] = (count, reset_at)
        return RateLimitResult(
            allowed=count <= limit,
            remaining=max(0, limit - count),
            reset_seconds=max(0, int(reset_at - now)),
        )


class RedisRateLimiter:
    def __init__(self, redis_url: str, key_prefix: str = "rate-limit"):
        try:
            from redis.asyncio import Redis
        except ImportError as exc:
            raise RuntimeError("Install redis to use Redis-backed rate limiting") from exc

        self._client = Redis.from_url(redis_url, decode_responses=True)
        self.key_prefix = key_prefix

    async def check(self, key: str, limit: int, window_seconds: int) -> RateLimitResult:
        redis_key = f"{self.key_prefix}:{key}"
        count = await self._client.incr(redis_key)
        if count == 1:
            await self._client.expire(redis_key, window_seconds)
        ttl = await self._client.ttl(redis_key)
        reset_seconds = window_seconds if ttl < 0 else ttl
        return RateLimitResult(
            allowed=count <= limit,
            remaining=max(0, limit - count),
            reset_seconds=reset_seconds,
        )
