import json
from collections.abc import AsyncIterator
from typing import Any

from app.agent.events import Event
from app.agent.parser import ParseError, ReActParser
from app.agent.prompts import PromptRenderer
from app.context.manager import ContextManager
from app.llm.client import StreamingLLM
from app.llm.token_counter import count_tokens
from app.tools.base import ToolError
from app.tools.registry import ToolRegistry


class ReActExecutor:
    def __init__(
        self,
        llm: StreamingLLM,
        registry: ToolRegistry,
        ctx: ContextManager,
        max_steps: int = 6,
        prompt_renderer: PromptRenderer | None = None,
    ):
        self.llm = llm
        self.registry = registry
        self.ctx = ctx
        self.max_steps = max_steps
        self.prompt_renderer = prompt_renderer or PromptRenderer()

    async def run(self, session_id: str, user_input: str, metadata: dict[str, Any] | None = None) -> AsyncIterator[Event]:
        history = await self.ctx.load(session_id)
        user_message = {"role": "user", "content": user_input, "metadata": metadata or {}}
        history.append(user_message)
        tool_calls = 0
        output_tokens = 0

        for step in range(self.max_steps):
            prompt_messages = self._build_messages(history)
            buffer = ""
            async for token in self.llm.stream(prompt_messages):
                buffer += token
                output_tokens += count_tokens(token)
                yield Event(type="thinking", data={"token": token})

            try:
                parsed = ReActParser.parse(buffer)
            except ParseError as exc:
                history.append({"role": "assistant", "content": buffer})
                history.append({"role": "tool", "content": f"ParserError: {exc}"})
                continue

            if parsed.is_final:
                answer = parsed.answer or ""
                output_tokens += count_tokens(answer)
                yield Event(type="final", data={"token": answer})
                await self.ctx.save(session_id, [*history, {"role": "assistant", "content": answer}])
                yield Event(
                    type="done",
                    data=self._stats(session_id, step + 1, tool_calls, output_tokens, history),
                )
                return

            yield Event(type="tool_start", data={"tool": parsed.action, "args": parsed.args or {}})
            tool_calls += 1
            try:
                observation = await self.registry.invoke(parsed.action or "", parsed.args or {})
            except ToolError as exc:
                observation = {"status": "error", "error": str(exc)}

            yield Event(type="tool_end", data={"tool": parsed.action, "result": observation})
            history.append({"role": "assistant", "content": buffer})
            history.append({"role": "tool", "name": parsed.action, "content": json.dumps(observation, ensure_ascii=False)})

        fallback = "抱歉, 任务步骤过多或模型输出无法解析, 请分步描述。"
        output_tokens += count_tokens(fallback)
        yield Event(type="final", data={"token": fallback})
        await self.ctx.save(session_id, [*history, {"role": "assistant", "content": fallback}])
        yield Event(
            type="done",
            data=self._stats(session_id, self.max_steps, tool_calls, output_tokens, history),
        )

    def _build_messages(self, history: list[dict[str, Any]]) -> list[dict[str, Any]]:
        system = self.prompt_renderer.render_system_prompt(self.registry.list_schemas())
        return [{"role": "system", "content": system}, *history]

    @staticmethod
    def _stats(
        session_id: str,
        steps: int,
        tool_calls: int,
        output_tokens: int,
        history: list[dict[str, Any]],
    ) -> dict[str, Any]:
        input_tokens = sum(count_tokens(str(message.get("content", ""))) for message in history)
        return {
            "session_id": session_id,
            "steps": steps,
            "tool_calls": tool_calls,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": input_tokens + output_tokens,
        }
