import asyncio
import json

import httpx

from app.tools.info.weather import HTTPWeatherProvider, StaticWeatherProvider, WeatherTool


def test_weather_tool_uses_static_provider():
    async def run():
        return await WeatherTool(StaticWeatherProvider()).execute("上海")

    result = asyncio.run(run())

    assert result["city"] == "上海"
    assert result["condition"] == "晴"


def test_http_weather_provider_queries_endpoint():
    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.params["city"] == "杭州"
        return httpx.Response(200, json={"condition": "雨", "temperature": 20})

    async def run():
        client = httpx.AsyncClient(transport=httpx.MockTransport(handler), base_url="http://weather")
        provider = HTTPWeatherProvider("http://weather", client=client)
        return await provider.query("杭州")

    result = asyncio.run(run())

    assert result["status"] == "ok"
    assert result["city"] == "杭州"
    assert result["condition"] == "雨"
