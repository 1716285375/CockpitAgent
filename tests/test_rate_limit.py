import asyncio

from app.auth.rate_limit import MemoryRateLimiter


def test_memory_rate_limiter_allows_until_limit():
    limiter = MemoryRateLimiter()

    async def run():
        first = await limiter.check("user-1", 2, 60)
        second = await limiter.check("user-1", 2, 60)
        third = await limiter.check("user-1", 2, 60)
        return first, second, third

    first, second, third = asyncio.run(run())

    assert first.allowed is True
    assert first.remaining == 1
    assert second.allowed is True
    assert second.remaining == 0
    assert third.allowed is False
    assert third.remaining == 0


def test_memory_rate_limiter_scopes_keys_independently():
    limiter = MemoryRateLimiter()

    async def run():
        first = await limiter.check("user-1", 1, 60)
        second = await limiter.check("user-2", 1, 60)
        return first, second

    first, second = asyncio.run(run())

    assert first.allowed is True
    assert second.allowed is True
