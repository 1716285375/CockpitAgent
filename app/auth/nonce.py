import time
from typing import Protocol


class NonceStore(Protocol):
    async def mark_seen(self, nonce: str, ttl_seconds: int) -> bool:
        """Return True when the nonce was not seen before."""
        ...


class MemoryNonceStore:
    def __init__(self):
        self._nonces: dict[str, float] = {}

    async def mark_seen(self, nonce: str, ttl_seconds: int) -> bool:
        now = time.time()
        self._purge_expired(now)
        if nonce in self._nonces:
            return False
        self._nonces[nonce] = now + ttl_seconds
        return True

    def _purge_expired(self, now: float) -> None:
        expired = [nonce for nonce, expires_at in self._nonces.items() if expires_at <= now]
        for nonce in expired:
            self._nonces.pop(nonce, None)


class RedisNonceStore:
    def __init__(self, redis_url: str, key_prefix: str = "nonce"):
        try:
            from redis.asyncio import Redis
        except ImportError as exc:
            raise RuntimeError("Install redis to use Redis-backed nonce storage") from exc

        self._client = Redis.from_url(redis_url, decode_responses=True)
        self.key_prefix = key_prefix

    async def mark_seen(self, nonce: str, ttl_seconds: int) -> bool:
        result = await self._client.set(self._key(nonce), "1", ex=ttl_seconds, nx=True)
        return bool(result)

    def _key(self, nonce: str) -> str:
        return f"{self.key_prefix}:{nonce}"
