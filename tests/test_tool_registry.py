import pytest
import asyncio

from app.tools import build_default_registry
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
