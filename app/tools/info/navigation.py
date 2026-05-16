from typing import Any, Protocol

import httpx
from pydantic import BaseModel, Field

from app.tools.base import BaseTool


class NavigationArgs(BaseModel):
    destination: str = Field(min_length=1, description="目的地或 POI")
    origin: str = Field(default="当前位置", description="起点")


class NavigationProvider(Protocol):
    async def route(self, destination: str, origin: str = "当前位置") -> dict[str, Any]:
        ...


class StaticNavigationProvider:
    async def route(self, destination: str, origin: str = "当前位置") -> dict[str, Any]:
        return {
            "status": "ok",
            "origin": origin,
            "destination": destination,
            "distance_km": 12.4,
            "eta_minutes": 28,
            "route": "推荐路线",
        }


class HTTPNavigationProvider:
    def __init__(self, base_url: str, api_key: str = "", client: httpx.AsyncClient | None = None):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.client = client or httpx.AsyncClient(timeout=5.0)

    async def route(self, destination: str, origin: str = "当前位置") -> dict[str, Any]:
        headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
        response = await self.client.get(
            f"{self.base_url}/route",
            params={"origin": origin, "destination": destination},
            headers=headers,
        )
        response.raise_for_status()
        data = response.json()
        data.setdefault("status", "ok")
        data.setdefault("origin", origin)
        data.setdefault("destination", destination)
        return data


class NavigationTool(BaseTool):
    name = "navigation"
    description = "查询目的地路线和预计用时"
    args_schema = NavigationArgs

    def __init__(self, provider: NavigationProvider | None = None):
        self.provider = provider or StaticNavigationProvider()

    async def execute(self, destination: str, origin: str = "当前位置") -> dict:
        return await self.provider.route(destination=destination, origin=origin)
