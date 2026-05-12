import asyncio

from app.auth.nonce import MemoryNonceStore


def test_memory_nonce_store_rejects_replay():
    store = MemoryNonceStore()

    async def run():
        first = await store.mark_seen("n1", 60)
        second = await store.mark_seen("n1", 60)
        return first, second

    first, second = asyncio.run(run())

    assert first is True
    assert second is False


def test_memory_nonce_store_allows_after_expiry():
    store = MemoryNonceStore()

    async def run():
        first = await store.mark_seen("n1", 0)
        second = await store.mark_seen("n1", 60)
        return first, second

    first, second = asyncio.run(run())

    assert first is True
    assert second is True
