import asyncio
from collections import defaultdict
from copy import deepcopy

from app.context.compressor import SimpleCompressor
from app.llm.token_counter import count_tokens


class ContextManager:
    def __init__(self, max_tokens: int = 3000, keep_recent: int = 4, compressor: SimpleCompressor | None = None):
        self.max_tokens = max_tokens
        self.keep_recent = keep_recent
        self.compressor = compressor or SimpleCompressor()
        self._store: dict[str, list[dict]] = {}
        self._locks: defaultdict[str, asyncio.Lock] = defaultdict(asyncio.Lock)

    async def load(self, session_id: str) -> list[dict]:
        return deepcopy(self._store.get(session_id, []))

    async def save(self, session_id: str, messages: list[dict]) -> None:
        async with self._locks[session_id]:
            self._store[session_id] = await self._maybe_compress(messages)

    async def append(self, session_id: str, *messages: dict) -> list[dict]:
        async with self._locks[session_id]:
            current = deepcopy(self._store.get(session_id, []))
            current.extend(messages)
            self._store[session_id] = await self._maybe_compress(current)
            return deepcopy(self._store[session_id])

    async def clear(self, session_id: str) -> None:
        async with self._locks[session_id]:
            self._store.pop(session_id, None)

    async def _maybe_compress(self, messages: list[dict]) -> list[dict]:
        total = sum(count_tokens(str(m.get("content", ""))) for m in messages)
        if total <= self.max_tokens or len(messages) <= self.keep_recent:
            return deepcopy(messages)

        old = messages[:-self.keep_recent]
        recent = messages[-self.keep_recent :]
        summary = await self.compressor.compress(old)
        return [{"role": "system", "content": f"[历史摘要] {summary}"}, *deepcopy(recent)]

