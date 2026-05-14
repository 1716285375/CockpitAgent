import asyncio
import json
import re
from collections.abc import AsyncIterator
from typing import Any, Protocol

import httpx

from app.llm.retry import CircuitBreaker, retry_async


class StreamingLLM(Protocol):
    async def stream(self, messages: list[dict[str, Any]]) -> AsyncIterator[str]:
        ...


class OpenAICompatibleLLMClient:
    def __init__(
        self,
        base_url: str,
        api_key: str,
        model: str,
        timeout: float = 30.0,
        max_retries: int = 3,
        circuit_breaker: CircuitBreaker | None = None,
        client: httpx.AsyncClient | None = None,
    ):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.client = client or httpx.AsyncClient(timeout=timeout)
        self.max_retries = max_retries
        self.circuit_breaker = circuit_breaker or CircuitBreaker()

    async def stream(self, messages: list[dict[str, Any]]) -> AsyncIterator[str]:
        self.circuit_breaker.before_call()
        try:
            tokens = await retry_async(
                lambda: self._collect_stream(messages),
                attempts=self.max_retries,
                retry_exceptions=(httpx.TimeoutException, httpx.HTTPStatusError, httpx.TransportError),
            )
        except Exception:
            self.circuit_breaker.record_failure()
            raise
        self.circuit_breaker.record_success()
        for token in tokens:
            yield token

    async def _collect_stream(self, messages: list[dict[str, Any]]) -> list[str]:
        headers = self._headers()
        payload = self._payload(messages, stream=True)
        tokens: list[str] = []
        async with self.client.stream("POST", f"{self.base_url}/chat/completions", headers=headers, json=payload) as resp:
            resp.raise_for_status()
            async for line in resp.aiter_lines():
                if not line.startswith("data: "):
                    continue
                chunk = line[6:].strip()
                if chunk == "[DONE]":
                    break
                data = json.loads(chunk)
                delta = data.get("choices", [{}])[0].get("delta", {})
                token = delta.get("content")
                if token:
                    tokens.append(token)
        return tokens

    async def complete(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        self.circuit_breaker.before_call()
        try:
            message = await retry_async(
                lambda: self._complete_once(messages, tools),
                attempts=self.max_retries,
                retry_exceptions=(httpx.TimeoutException, httpx.HTTPStatusError, httpx.TransportError),
            )
        except Exception:
            self.circuit_breaker.record_failure()
            raise
        self.circuit_breaker.record_success()
        return message

    async def _complete_once(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        response = await self.client.post(
            f"{self.base_url}/chat/completions",
            headers=self._headers(),
            json=self._payload(messages, stream=False, tools=tools),
        )
        response.raise_for_status()
        data = response.json()
        return data.get("choices", [{}])[0].get("message", {})

    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}

    def _payload(
        self,
        messages: list[dict[str, Any]],
        *,
        stream: bool,
        tools: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {"model": self.model, "messages": messages, "stream": stream}
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"
        return payload


class HeuristicLLMClient:
    """Local fallback for demos and tests when no model API key is configured."""

    async def stream(self, messages: list[dict[str, Any]]) -> AsyncIterator[str]:
        text = self._decide(messages)
        for token in self._tokenize(text):
            await asyncio.sleep(0)
            yield token

    def _decide(self, messages: list[dict[str, Any]]) -> str:
        last_user = self._last_content(messages, "user")
        observations = [m for m in messages if m.get("role") == "tool"]
        completed_tools = {str(m.get("name", "")) for m in observations}

        if "ac_control" not in completed_tools and any(word in last_user for word in ["空调", "温度", "制冷", "制热"]):
            temp = self._extract_temperature(last_user) or 22
            return f'Thought: 需要先控制空调。\nAction: ac_control\nAction Input: {{"temperature": {temp}, "mode": "auto"}}'

        if "weather" not in completed_tools and any(word in last_user for word in ["天气", "下雨", "气温"]):
            city = self._extract_city(last_user) or "上海"
            return f'Thought: 需要查询天气。\nAction: weather\nAction Input: {{"city": "{city}"}}'

        if "navigation" not in completed_tools and any(word in last_user for word in ["导航", "去", "路线", "怎么走"]):
            destination = self._extract_destination(last_user) or "目的地"
            return f'Thought: 需要规划路线。\nAction: navigation\nAction Input: {{"destination": "{destination}"}}'

        if "vehicle_status" not in completed_tools and any(word in last_user for word in ["胎压", "电量", "油量", "里程", "车辆状态"]):
            return 'Thought: 需要查询车辆状态。\nAction: vehicle_status\nAction Input: {"item": "all"}'

        if "play_music" not in completed_tools and any(word in last_user for word in ["音乐", "播放", "暂停", "下一首"]):
            return f'Thought: 需要控制媒体播放。\nAction: play_music\nAction Input: {{"action": "play", "query": "{last_user}"}}'

        if observations:
            return f"Final Answer: {self._final_answer(observations)}"

        return "Final Answer: 我可以帮你控制空调、车窗、座椅，查询天气、导航和车辆状态。"

    @staticmethod
    def _last_content(messages: list[dict[str, Any]], role: str) -> str:
        for message in reversed(messages):
            if message.get("role") == role:
                return str(message.get("content", ""))
        return ""

    @staticmethod
    def _extract_temperature(text: str) -> int | None:
        match = re.search(r"(\d{2})\s*度?", text)
        if not match:
            return None
        value = int(match.group(1))
        return min(32, max(16, value))

    @staticmethod
    def _extract_city(text: str) -> str | None:
        match = re.search(r"([\u4e00-\u9fa5]{2,8})(?:的)?天气", text)
        return match.group(1) if match else None

    @staticmethod
    def _extract_destination(text: str) -> str | None:
        match = re.search(r"(?:导航到|去|到)([\u4e00-\u9fa5A-Za-z0-9\s]{2,20})", text)
        return match.group(1).strip() if match else None

    @staticmethod
    def _final_answer(observations: list[dict[str, Any]]) -> str:
        parts: list[str] = []
        for observation in observations:
            name = str(observation.get("name", ""))
            content = str(observation.get("content", ""))
            data = {}
            try:
                data = json.loads(content)
            except json.JSONDecodeError:
                pass

            if name == "ac_control" or "AC_SET" in content:
                parts.append("空调已按你的要求设置。")
            elif name == "weather" or ("condition" in content and "temperature" in content):
                city = data.get("city", "当地")
                condition = data.get("condition", "已获取")
                temperature = data.get("temperature")
                temp_text = f"{temperature}度" if temperature is not None else ""
                parts.append(f"{city}天气{condition}{temp_text}。")
            elif name == "navigation" or "eta_minutes" in content:
                eta = data.get("eta_minutes")
                eta_text = f", 预计{eta}分钟" if eta else ""
                parts.append(f"路线已规划完成{eta_text}。")
            else:
                parts.append("操作已完成。")
        return "".join(parts)

    @staticmethod
    def _tokenize(text: str) -> list[str]:
        return [text[i : i + 8] for i in range(0, len(text), 8)]
