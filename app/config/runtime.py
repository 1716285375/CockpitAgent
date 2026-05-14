from collections.abc import Mapping
from typing import Any

from app.agent.executor import ReActExecutor
from app.tools.registry import ToolRegistry


def apply_runtime_config(
    payload: Mapping[str, Any],
    *,
    executor: ReActExecutor,
    registry: ToolRegistry,
) -> dict[str, Any]:
    changes: dict[str, Any] = {}

    max_steps = _get(payload, "agent.max_steps", "agent_max_steps")
    if max_steps is not None:
        executor.max_steps = int(max_steps)
        changes["agent.max_steps"] = executor.max_steps

    prompt_template = _get(payload, "prompt.system_template", "prompt_template")
    if prompt_template is not None:
        executor.prompt_renderer.template = str(prompt_template)
        changes["prompt.system_template"] = "updated"

    enabled_tools = _get(payload, "tools.enabled", "tools_enabled")
    if enabled_tools is not None:
        enabled = _normalize_tool_names(enabled_tools)
        for tool in registry.list_tools():
            registry.set_enabled(tool["name"], tool["name"] in enabled)
        changes["tools.enabled"] = sorted(enabled)

    return changes


def _get(payload: Mapping[str, Any], dotted_key: str, flat_key: str) -> Any:
    if flat_key in payload:
        return payload[flat_key]
    if dotted_key in payload:
        return payload[dotted_key]
    current: Any = payload
    for part in dotted_key.split("."):
        if not isinstance(current, Mapping) or part not in current:
            return None
        current = current[part]
    return current


def _normalize_tool_names(value: Any) -> set[str]:
    if isinstance(value, str):
        return {item.strip() for item in value.split(",") if item.strip()}
    if isinstance(value, (list, tuple, set)):
        return {str(item).strip() for item in value if str(item).strip()}
    raise ValueError("tools.enabled must be a comma-separated string or list")
