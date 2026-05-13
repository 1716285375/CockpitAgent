import asyncio

import httpx

from app.config.nacos_client import NacosConfigClient, parse_config_payload


def test_parse_config_payload_accepts_json():
    result = parse_config_payload('{"llm_model":"qwen-max","agent_max_steps":6}')

    assert result == {"llm_model": "qwen-max", "agent_max_steps": 6}


def test_parse_config_payload_accepts_key_value_lines():
    result = parse_config_payload("llm_model=qwen-max\nagent_max_steps=6")

    assert result == {"llm_model": "qwen-max", "agent_max_steps": "6"}


def test_nacos_config_client_fetches_config():
    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.params["dataId"] == "cockpit-agent"
        assert request.url.params["group"] == "DEFAULT_GROUP"
        return httpx.Response(200, text='{"agent_max_steps": 4}')

    async def run():
        client = httpx.AsyncClient(transport=httpx.MockTransport(handler), base_url="http://nacos")
        nacos = NacosConfigClient("http://nacos", "cockpit-agent", client=client)
        return await nacos.get_config()

    assert asyncio.run(run()) == '{"agent_max_steps": 4}'
