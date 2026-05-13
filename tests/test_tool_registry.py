import pytest
import asyncio
from pydantic import BaseModel

from app.tools import build_default_registry
from app.tools.base import BaseTool
from app.tools.base import ToolError


def test_tool_registry_invokes_ac_control():
    registry = build_default_registry()

    result = asyncio.run(registry.invoke("ac_control", {"temperature": 22, "mode": "auto"}))

    assert result["status"] == "ok"
    assert result["current_temp"] == 22


def test_tool_registry_validates_args():
    registry = build_default_registry()

    with pytest.raises(ToolError):
        asyncio.run(registry.invoke("ac_control", {"temperature": 100}))


def test_tool_registry_caches_identical_calls():
    class Args(BaseModel):
        value: int

    class CountingTool(BaseTool):
        name = "counting"
        description = "Counting test tool"
        args_schema = Args

        def __init__(self):
            self.calls = 0

        async def execute(self, value: int) -> dict:
            self.calls += 1
            return {"status": "ok", "value": value, "calls": self.calls}

    tool = CountingTool()
    registry = build_default_registry(cache_ttl_seconds=60)
    registry.register(tool)

    first = asyncio.run(registry.invoke("counting", {"value": 1}))
    second = asyncio.run(registry.invoke("counting", {"value": 1}))

    assert first == second
    assert tool.calls == 1


def test_tool_registry_cache_can_be_disabled():
    class Args(BaseModel):
        value: int

    class CountingTool(BaseTool):
        name = "uncached_counting"
        description = "Uncached counting test tool"
        args_schema = Args

        def __init__(self):
            self.calls = 0

        async def execute(self, value: int) -> dict:
            self.calls += 1
            return {"status": "ok", "value": value, "calls": self.calls}

    tool = CountingTool()
    registry = build_default_registry(cache_ttl_seconds=0)
    registry.register(tool)

    first = asyncio.run(registry.invoke("uncached_counting", {"value": 1}))
    second = asyncio.run(registry.invoke("uncached_counting", {"value": 1}))

    assert first["calls"] == 1
    assert second["calls"] == 2
