from app.agent.prompts import PromptRenderer


def test_prompt_renderer_injects_tool_schema():
    renderer = PromptRenderer("Tools:\n{tools}")

    prompt = renderer.render_system_prompt([{"name": "weather", "parameters": {"type": "object"}}])

    assert "weather" in prompt
    assert '"parameters"' in prompt


def test_prompt_renderer_uses_default_when_file_missing(tmp_path):
    renderer = PromptRenderer.from_file(tmp_path / "missing.tmpl")

    prompt = renderer.render_system_prompt([])

    assert "ReAct" in prompt
