import asyncio
import json
import time
from collections.abc import Iterable
from copy import deepcopy
from typing import Any

from pydantic import ValidationError

from app.tools.base import BaseTool, ToolError


class ToolRegistry:
    def __init__(self, timeout_seconds: float = 5.0, cache_ttl_seconds: float = 10.0):
        self.timeout_seconds = timeout_seconds
        self.cache_ttl_seconds = cache_ttl_seconds
        self._tools: dict[str, BaseTool] = {}
        self._cache: dict[str, tuple[float, dict[str, Any]]] = {}

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

        cache_key = self._cache_key(name, validated.model_dump())
        cached = self._read_cache(cache_key)
        if cached is not None:
            return cached

        try:
            result = await asyncio.wait_for(
                tool.execute(**validated.model_dump()),
                timeout=self.timeout_seconds,
            )
        except TimeoutError as exc:
            raise ToolError(f"Tool {name} timeout") from exc
        self._write_cache(cache_key, result)
        return deepcopy(result)

    def list_schemas(self) -> list[dict[str, Any]]:
        return [tool.schema() for tool in self._tools.values() if tool.enabled]

    def list_tools(self) -> list[dict[str, Any]]:
        return [
            {"name": tool.name, "description": tool.description, "enabled": tool.enabled}
            for tool in self._tools.values()
        ]

    def set_enabled(self, name: str, enabled: bool) -> None:
        self.get(name).enabled = enabled
        self.clear_cache(tool_name=name)

    def clear_cache(self, tool_name: str | None = None) -> None:
        if tool_name is None:
            self._cache.clear()
            return
        prefix = f"{tool_name}:"
        keys = [key for key in self._cache if key.startswith(prefix)]
        for key in keys:
            self._cache.pop(key, None)

    def _read_cache(self, key: str) -> dict[str, Any] | None:
        if self.cache_ttl_seconds <= 0:
            return None
        cached = self._cache.get(key)
        if cached is None:
            return None
        expires_at, value = cached
        if expires_at <= time.monotonic():
            self._cache.pop(key, None)
            return None
        return deepcopy(value)

    def _write_cache(self, key: str, value: dict[str, Any]) -> None:
        if self.cache_ttl_seconds <= 0:
            return
        self._cache[key] = (time.monotonic() + self.cache_ttl_seconds, deepcopy(value))

    @staticmethod
    def _cache_key(name: str, args: dict[str, Any]) -> str:
        return f"{name}:{json.dumps(args, ensure_ascii=False, sort_keys=True, separators=(',', ':'))}"
