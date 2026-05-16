import pytest
import asyncio
from pydantic import BaseModel

from app.tools import build_default_registry
from app.tools.base import BaseTool
from app.tools.base import DisabledToolError, ToolValidationError, UnknownToolError


def test_tool_registry_invokes_ac_control():
    registry = build_default_registry()

    result = asyncio.run(registry.invoke("ac_control", {"temperature": 22, "mode": "auto"}))

    assert result["status"] == "ok"
    assert result["current_temp"] == 22


def test_tool_registry_validates_args():
    registry = build_default_registry()

    with pytest.raises(ToolValidationError):
        asyncio.run(registry.invoke("ac_control", {"temperature": 100}))


def test_tool_registry_classifies_unknown_tools():
    registry = build_default_registry()

    with pytest.raises(UnknownToolError):
        asyncio.run(registry.invoke("missing_tool", {}))


def test_tool_registry_classifies_disabled_tools():
    registry = build_default_registry()
    registry.set_enabled("weather", False)

    with pytest.raises(DisabledToolError):
        asyncio.run(registry.invoke("weather", {"city": "上海"}))


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


def test_tool_registry_exports_openai_tool_schemas():
    registry = build_default_registry()

    schemas = registry.list_openai_tools()

    assert schemas
    assert schemas[0]["type"] == "function"
    assert "name" in schemas[0]["function"]
    assert "parameters" in schemas[0]["function"]


def test_tool_registry_describes_runtime():
    registry = build_default_registry(cache_ttl_seconds=7)

    runtime = registry.describe_runtime()

    assert runtime["tools"] >= 1
    assert runtime["cache_ttl_seconds"] == 7
    assert "weather" in runtime["enabled_tools"]
