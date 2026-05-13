import asyncio

from app.context.session_lock import MemorySessionLock


def test_memory_session_lock_rejects_concurrent_acquire():
    lock = MemorySessionLock()

    async def run():
        first = await lock.acquire("s1", 60)
        second = await lock.acquire("s1", 60)
        return first, second

    first, second = asyncio.run(run())

    assert first is True
    assert second is False


def test_memory_session_lock_releases_session():
    lock = MemorySessionLock()

    async def run():
        first = await lock.acquire("s1", 60)
        await lock.release("s1")
        second = await lock.acquire("s1", 60)
        return first, second

    first, second = asyncio.run(run())

    assert first is True
    assert second is True
