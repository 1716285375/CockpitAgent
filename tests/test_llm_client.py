import asyncio
import json

import httpx

from app.llm.client import OpenAICompatibleLLMClient


def test_openai_client_complete_returns_message():
    async def handler(request: httpx.Request) -> httpx.Response:
        payload = json.loads(request.content)
        assert payload["stream"] is False
        assert payload["tools"][0]["type"] == "function"
        return httpx.Response(
            200,
            json={
                "choices": [
                    {
                        "message": {
                            "role": "assistant",
                            "tool_calls": [
                                {
                                    "type": "function",
                                    "function": {"name": "weather", "arguments": '{"city":"上海"}'},
                                }
                            ],
                        }
                    }
                ]
            },
        )

    async def run():
        http_client = httpx.AsyncClient(transport=httpx.MockTransport(handler), base_url="http://llm")
        client = OpenAICompatibleLLMClient("http://llm", "key", "model", client=http_client)
        return await client.complete(
            [{"role": "user", "content": "weather"}],
            tools=[{"type": "function", "function": {"name": "weather", "parameters": {}}}],
        )

    message = asyncio.run(run())

    assert message["tool_calls"][0]["function"]["name"] == "weather"


def test_openai_client_payload_omits_tools_when_empty():
    client = OpenAICompatibleLLMClient("http://llm", "key", "model")

    payload = client._payload([{"role": "user", "content": "hi"}], stream=False, tools=[])

    assert "tools" not in payload
