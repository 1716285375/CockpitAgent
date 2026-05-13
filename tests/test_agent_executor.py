import asyncio

from app.agent.executor import ReActExecutor
from app.agent.prompts import PromptRenderer
from app.context.manager import ContextManager
from app.llm.client import HeuristicLLMClient
from app.tools import build_default_registry


def test_executor_runs_tool_and_returns_final_answer():
    executor = ReActExecutor(
        llm=HeuristicLLMClient(),
        registry=build_default_registry(),
        ctx=ContextManager(),
        max_steps=4,
    )

    async def collect():
        return [event async for event in executor.run("s1", "把空调调到22度")]

    events = asyncio.run(collect())
    event_types = [event.type for event in events]

    assert "tool_start" in event_types
    assert "tool_end" in event_types
    assert event_types[-2] == "final"
    assert event_types[-1] == "done"
    assert "空调" in events[-2].data["token"]
    assert events[-1].data["tool_calls"] == 1


def test_executor_runs_multiple_tools():
    executor = ReActExecutor(
        llm=HeuristicLLMClient(),
        registry=build_default_registry(),
        ctx=ContextManager(),
        max_steps=4,
    )

    async def collect():
        return [event async for event in executor.run("s2", "把空调调到22度，然后查一下上海天气")]

    events = asyncio.run(collect())
    tool_names = [event.data["tool"] for event in events if event.type == "tool_start"]

    assert tool_names == ["ac_control", "weather"]
    assert "天气" in events[-2].data["token"]
    assert events[-1].type == "done"
    assert events[-1].data["tool_calls"] == 2


def test_executor_builds_messages_from_prompt_template():
    executor = ReActExecutor(
        llm=HeuristicLLMClient(),
        registry=build_default_registry(),
        ctx=ContextManager(),
        prompt_renderer=PromptRenderer("Custom tools: {tools}"),
    )

    messages = executor._build_messages([])

    assert messages[0]["content"].startswith("Custom tools:")
    assert "ac_control" in messages[0]["content"]
