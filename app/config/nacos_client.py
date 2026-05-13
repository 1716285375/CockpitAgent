import asyncio
import json
from collections.abc import Awaitable, Callable
from typing import Any

import httpx


class NacosConfigClient:
    def __init__(
        self,
        server: str,
        data_id: str,
        group: str = "DEFAULT_GROUP",
        namespace: str = "",
        timeout: float = 5.0,
        client: httpx.AsyncClient | None = None,
    ):
        self.server = server.rstrip("/")
        self.data_id = data_id
        self.group = group
        self.namespace = namespace
        self.client = client or httpx.AsyncClient(timeout=timeout)

    async def get_config(self) -> str:
        params = {"dataId": self.data_id, "group": self.group}
        if self.namespace:
            params["tenant"] = self.namespace
        response = await self.client.get(f"{self.server}/nacos/v1/cs/configs", params=params)
        response.raise_for_status()
        return response.text

    async def watch_config(
        self,
        on_change: Callable[[dict[str, Any]], Awaitable[None]],
        *,
        poll_interval_seconds: float = 5.0,
        stop_after_polls: int | None = None,
    ) -> None:
        last_payload: str | None = None
        polls = 0
        while stop_after_polls is None or polls < stop_after_polls:
            payload = await self.get_config()
            if payload != last_payload:
                await on_change(parse_config_payload(payload))
                last_payload = payload
            polls += 1
            await asyncio.sleep(poll_interval_seconds)


def parse_config_payload(payload: str) -> dict[str, Any]:
    payload = payload.strip()
    if not payload:
        return {}
    try:
        data = json.loads(payload)
        if isinstance(data, dict):
            return data
        raise ValueError("Nacos JSON config must be an object")
    except json.JSONDecodeError:
        return _parse_key_value_payload(payload)


def _parse_key_value_payload(payload: str) -> dict[str, str]:
    result: dict[str, str] = {}
    for line in payload.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if "=" not in stripped:
            raise ValueError(f"Invalid config line: {line}")
        key, value = stripped.split("=", 1)
        result[key.strip()] = value.strip()
    return result
