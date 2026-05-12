import asyncio
from collections import defaultdict
from copy import deepcopy

from app.context.compressor import SimpleCompressor
from app.context.store import ContextStore, MemoryContextStore
from app.llm.token_counter import count_tokens


class ContextManager:
    def __init__(
        self,
        max_tokens: int = 3000,
        keep_recent: int = 4,
        ttl_seconds: int = 86400,
        compressor: SimpleCompressor | None = None,
        store: ContextStore | None = None,
    ):
        self.max_tokens = max_tokens
        self.keep_recent = keep_recent
        self.ttl_seconds = ttl_seconds
        self.compressor = compressor or SimpleCompressor()
        self.store = store or MemoryContextStore()
        self._locks: defaultdict[str, asyncio.Lock] = defaultdict(asyncio.Lock)

    async def load(self, session_id: str) -> list[dict]:
        return await self.store.load(session_id)

    async def save(self, session_id: str, messages: list[dict]) -> None:
        async with self._locks[session_id]:
            compressed = await self._maybe_compress(messages)
            await self.store.save(session_id, compressed, self.ttl_seconds)

    async def append(self, session_id: str, *messages: dict) -> list[dict]:
        async with self._locks[session_id]:
            current = await self.store.load(session_id)
            current.extend(messages)
            compressed = await self._maybe_compress(current)
            await self.store.save(session_id, compressed, self.ttl_seconds)
            return deepcopy(compressed)

    async def clear(self, session_id: str) -> None:
        async with self._locks[session_id]:
            await self.store.clear(session_id)

    async def _maybe_compress(self, messages: list[dict]) -> list[dict]:
        total = sum(count_tokens(str(m.get("content", ""))) for m in messages)
        if total <= self.max_tokens or len(messages) <= self.keep_recent:
            return deepcopy(messages)

        old = messages[:-self.keep_recent]
        recent = messages[-self.keep_recent :]
        summary = await self.compressor.compress(old)
        return [{"role": "system", "content": f"[历史摘要] {summary}"}, *deepcopy(recent)]
