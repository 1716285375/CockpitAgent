import json
from copy import deepcopy
from typing import Protocol


class ContextStore(Protocol):
    async def load(self, session_id: str) -> list[dict]:
        ...

    async def save(self, session_id: str, messages: list[dict], ttl_seconds: int) -> None:
        ...

    async def clear(self, session_id: str) -> None:
        ...


class MemoryContextStore:
    def __init__(self):
        self._data: dict[str, list[dict]] = {}

    async def load(self, session_id: str) -> list[dict]:
        return deepcopy(self._data.get(session_id, []))

    async def save(self, session_id: str, messages: list[dict], ttl_seconds: int) -> None:
        self._data[session_id] = deepcopy(messages)

    async def clear(self, session_id: str) -> None:
        self._data.pop(session_id, None)


class RedisContextStore:
    def __init__(self, redis_url: str, key_prefix: str = "session"):
        try:
            from redis.asyncio import Redis
        except ImportError as exc:
            raise RuntimeError("Install redis to use Redis-backed context storage") from exc

        self._client = Redis.from_url(redis_url, decode_responses=True)
        self.key_prefix = key_prefix

    async def load(self, session_id: str) -> list[dict]:
        raw = await self._client.get(self._key(session_id))
        if not raw:
            return []
        data = json.loads(raw)
        if not isinstance(data, list):
            return []
        return data

    async def save(self, session_id: str, messages: list[dict], ttl_seconds: int) -> None:
        payload = json.dumps(messages, ensure_ascii=False)
        await self._client.setex(self._key(session_id), ttl_seconds, payload)

    async def clear(self, session_id: str) -> None:
        await self._client.delete(self._key(session_id))

    def _key(self, session_id: str) -> str:
        return f"{self.key_prefix}:{session_id}"
