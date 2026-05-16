from typing import Any, Protocol

import httpx
from pydantic import BaseModel, Field

from app.tools.base import BaseTool


class WeatherArgs(BaseModel):
    city: str = Field(default="上海", min_length=1, description="城市名称")


class WeatherProvider(Protocol):
    async def query(self, city: str) -> dict[str, Any]:
        ...


class StaticWeatherProvider:
    async def query(self, city: str) -> dict[str, Any]:
        return {
            "status": "ok",
            "city": city,
            "condition": "晴",
            "temperature": 26,
            "unit": "celsius",
            "suggestion": "适合通勤, 注意防晒",
        }


class HTTPWeatherProvider:
    def __init__(self, base_url: str, api_key: str = "", client: httpx.AsyncClient | None = None):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.client = client or httpx.AsyncClient(timeout=5.0)

    async def query(self, city: str) -> dict[str, Any]:
        headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
        response = await self.client.get(f"{self.base_url}/weather", params={"city": city}, headers=headers)
        response.raise_for_status()
        data = response.json()
        data.setdefault("status", "ok")
        data.setdefault("city", city)
        return data


class WeatherTool(BaseTool):
    name = "weather"
    description = "查询指定城市的天气"
    args_schema = WeatherArgs

    def __init__(self, provider: WeatherProvider | None = None):
        self.provider = provider or StaticWeatherProvider()

    async def execute(self, city: str = "上海") -> dict:
        return await self.provider.query(city)
