import asyncio

from app.context.manager import ContextManager


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
