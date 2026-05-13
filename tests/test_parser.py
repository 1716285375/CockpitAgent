import pytest

from app.agent.parser import ParseError, ReActParser


def test_parser_reads_react_action():
    parsed = ReActParser.parse('Thought: query weather\nAction: weather\nAction Input: {"city":"上海"}')

    assert parsed.action == "weather"
    assert parsed.args == {"city": "上海"}


def test_parser_reads_final_answer():
    parsed = ReActParser.parse("Final Answer: 已完成")

    assert parsed.is_final is True
    assert parsed.answer == "已完成"


def test_parser_reads_openai_tool_call_message():
    parsed = ReActParser.parse_message(
        {
            "tool_calls": [
                {
                    "type": "function",
                    "function": {"name": "ac_control", "arguments": '{"temperature":22}'},
                }
            ]
        }
    )

    assert parsed.action == "ac_control"
    assert parsed.args == {"temperature": 22}


def test_parser_rejects_invalid_tool_call_arguments():
    with pytest.raises(ParseError):
        ReActParser.parse_message(
            {
                "tool_calls": [
                    {
                        "type": "function",
                        "function": {"name": "ac_control", "arguments": "{bad"},
                    }
                ]
            }
        )
