import asyncio
from collections.abc import Iterable
from typing import Any

from pydantic import ValidationError

from app.tools.base import BaseTool, ToolError


class ToolRegistry:
    def __init__(self, timeout_seconds: float = 5.0):
        self.timeout_seconds = timeout_seconds
        self._tools: dict[str, BaseTool] = {}

    def register(self, tool: BaseTool) -> BaseTool:
        if tool.name in self._tools:
            raise ValueError(f"Tool {tool.name} already registered")
        self._tools[tool.name] = tool
        return tool

    def register_many(self, tools: Iterable[BaseTool]) -> None:
        for tool in tools:
            self.register(tool)

    def get(self, name: str) -> BaseTool:
        try:
            return self._tools[name]
        except KeyError as exc:
            raise ToolError(f"Unknown tool: {name}") from exc

    async def invoke(self, name: str, args: dict[str, Any] | None = None) -> dict[str, Any]:
        tool = self.get(name)
        if not tool.enabled:
            raise ToolError(f"Tool {name} is disabled")

        try:
            validated = tool.args_schema(**(args or {}))
        except ValidationError as exc:
            raise ToolError(f"Args validation failed: {exc}") from exc

        try:
            return await asyncio.wait_for(
                tool.execute(**validated.model_dump()),
                timeout=self.timeout_seconds,
            )
        except TimeoutError as exc:
            raise ToolError(f"Tool {name} timeout") from exc

    def list_schemas(self) -> list[dict[str, Any]]:
        return [tool.schema() for tool in self._tools.values() if tool.enabled]

    def list_tools(self) -> list[dict[str, Any]]:
        return [
            {"name": tool.name, "description": tool.description, "enabled": tool.enabled}
            for tool in self._tools.values()
        ]

    def set_enabled(self, name: str, enabled: bool) -> None:
        self.get(name).enabled = enabled

