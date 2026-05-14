from app.agent.executor import ReActExecutor
from app.agent.prompts import PromptRenderer
from app.config.runtime import apply_runtime_config
from app.context.manager import ContextManager
from app.llm.client import HeuristicLLMClient
from app.tools import build_default_registry


def test_apply_runtime_config_updates_executor_and_tools():
    registry = build_default_registry()
    executor = ReActExecutor(
        llm=HeuristicLLMClient(),
        registry=registry,
        ctx=ContextManager(),
        prompt_renderer=PromptRenderer("old {tools}"),
    )

    changes = apply_runtime_config(
        {
            "agent": {"max_steps": 2},
            "prompt": {"system_template": "new {tools}"},
            "tools": {"enabled": ["weather"]},
        },
        executor=executor,
        registry=registry,
    )

    assert changes["agent.max_steps"] == 2
    assert changes["prompt.system_template"] == "updated"
    assert executor.prompt_renderer.template == "new {tools}"
    enabled = [tool["name"] for tool in registry.list_tools() if tool["enabled"]]
    assert enabled == ["weather"]


def test_apply_runtime_config_accepts_flat_keys():
    registry = build_default_registry()
    executor = ReActExecutor(llm=HeuristicLLMClient(), registry=registry, ctx=ContextManager())

    changes = apply_runtime_config(
        {"agent_max_steps": "5", "tools_enabled": "weather,ac_control"},
        executor=executor,
        registry=registry,
    )

    assert changes["agent.max_steps"] == 5
    assert changes["tools.enabled"] == ["ac_control", "weather"]
