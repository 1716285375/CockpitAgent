import asyncio

import pytest

from app.tools import build_default_registry
from app.tools.base import ToolError


def test_preference_tools_read_written_values():
    registry = build_default_registry(cache_ttl_seconds=60)

    async def run():
        await registry.invoke(
            "set_user_preference",
            {"user_id": "u1", "key": "temperature", "value": "22"},
        )
        return await registry.invoke("get_user_preference", {"user_id": "u1", "key": "temperature"})

    result = asyncio.run(run())

    assert result["value"] == "22"


def test_preference_tools_do_not_return_stale_cached_values():
    registry = build_default_registry(cache_ttl_seconds=60)

    async def run():
        await registry.invoke("set_user_preference", {"user_id": "u1", "key": "mode", "value": "eco"})
        first = await registry.invoke("get_user_preference", {"user_id": "u1", "key": "mode"})
        await registry.invoke("set_user_preference", {"user_id": "u1", "key": "mode", "value": "sport"})
        second = await registry.invoke("get_user_preference", {"user_id": "u1", "key": "mode"})
        return first, second

    first, second = asyncio.run(run())

    assert first["value"] == "eco"
    assert second["value"] == "sport"


def test_preference_tools_raise_for_missing_key():
    registry = build_default_registry()

    async def run():
        await registry.invoke("get_user_preference", {"user_id": "u1", "key": "missing"})

    with pytest.raises(ToolError):
        asyncio.run(run())
