import json
from pathlib import Path
from typing import Any


DEFAULT_TEMPLATE = """你是智能座舱语音助手 Agent。你必须使用 ReAct 格式输出。

可用工具:
{tools}

规则:
1. 如果需要工具, 输出:
Thought: 简短说明
Action: tool_name
Action Input: 标准 JSON
2. 如果可以回答或工具结果已足够, 输出:
Final Answer: 给用户的简洁中文答复
3. Action Input 必须是标准 JSON, 不要使用 markdown 代码块。
"""


class PromptRenderer:
    def __init__(self, template: str | None = None):
        self.template = template or DEFAULT_TEMPLATE

    @classmethod
    def from_file(cls, path: str | Path) -> "PromptRenderer":
        template_path = Path(path)
        if not template_path.exists():
            return cls()
        return cls(template_path.read_text(encoding="utf-8"))

    def render_system_prompt(self, tools: list[dict[str, Any]]) -> str:
        rendered_tools = json.dumps(tools, ensure_ascii=False, indent=2)
        return self.template.format(tools=rendered_tools)
