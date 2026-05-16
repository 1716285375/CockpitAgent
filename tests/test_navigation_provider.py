import asyncio

import httpx

from app.tools.info.navigation import HTTPNavigationProvider, NavigationTool, StaticNavigationProvider


def test_navigation_tool_uses_static_provider():
    async def run():
        return await NavigationTool(StaticNavigationProvider()).execute("公司")

    result = asyncio.run(run())

    assert result["destination"] == "公司"
    assert result["eta_minutes"] == 28


def test_http_navigation_provider_queries_endpoint():
    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.params["origin"] == "家"
        assert request.url.params["destination"] == "公司"
        return httpx.Response(200, json={"distance_km": 9.8, "eta_minutes": 21})

    async def run():
        client = httpx.AsyncClient(transport=httpx.MockTransport(handler), base_url="http://map")
        provider = HTTPNavigationProvider("http://map", client=client)
        return await provider.route(origin="家", destination="公司")

    result = asyncio.run(run())

    assert result["status"] == "ok"
    assert result["origin"] == "家"
    assert result["destination"] == "公司"
    assert result["eta_minutes"] == 21
