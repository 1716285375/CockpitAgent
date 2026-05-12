import asyncio

from app.context.manager import ContextManager
from app.context.store import MemoryContextStore


def test_context_manager_compresses_long_history():
    ctx = ContextManager(max_tokens=20, keep_recent=2)
    messages = [{"role": "user", "content": "很长的历史内容" * 10} for _ in range(6)]

    async def run():
        await ctx.save("s1", messages)
        return await ctx.load("s1")

    saved = asyncio.run(run())

    assert saved[0]["role"] == "system"
    assert "[历史摘要]" in saved[0]["content"]
    assert len(saved) == 3


def test_context_manager_appends_and_clears_messages():
    ctx = ContextManager(store=MemoryContextStore())

    async def run():
        saved = await ctx.append("s1", {"role": "user", "content": "hello"})
        loaded = await ctx.load("s1")
        await ctx.clear("s1")
        cleared = await ctx.load("s1")
        return saved, loaded, cleared

    saved, loaded, cleared = asyncio.run(run())

    assert saved == [{"role": "user", "content": "hello"}]
    assert loaded == saved
    assert cleared == []
