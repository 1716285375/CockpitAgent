import json
import re
from dataclasses import dataclass
from typing import Any


class ParseError(ValueError):
    pass


@dataclass(frozen=True)
class ParsedOutput:
    thought: str | None = None
    action: str | None = None
    args: dict[str, Any] | None = None
    answer: str | None = None

    @property
    def is_final(self) -> bool:
        return self.answer is not None


class ReActParser:
    FINAL_RE = re.compile(r"Final Answer\s*:\s*(?P<answer>.*)", re.IGNORECASE | re.DOTALL)
    ACTION_RE = re.compile(r"Action\s*:\s*(?P<action>[a-zA-Z_][\w]*)", re.IGNORECASE)
    INPUT_RE = re.compile(r"Action Input\s*:\s*(?P<input>\{.*\})", re.IGNORECASE | re.DOTALL)
    THOUGHT_RE = re.compile(r"Thought\s*:\s*(?P<thought>.*?)(?:\nAction\s*:|\nFinal Answer\s*:|$)", re.IGNORECASE | re.DOTALL)

    @classmethod
    def parse(cls, text: str) -> ParsedOutput:
        cleaned = cls._strip_code_fences(text).strip()
        final = cls.FINAL_RE.search(cleaned)
        if final:
            return ParsedOutput(answer=final.group("answer").strip())

        action_match = cls.ACTION_RE.search(cleaned)
        input_match = cls.INPUT_RE.search(cleaned)
        if not action_match:
            raise ParseError("Missing Action or Final Answer in LLM output")

        raw_args = input_match.group("input") if input_match else "{}"
        try:
            args = json.loads(raw_args)
        except json.JSONDecodeError as exc:
            raise ParseError(f"Invalid Action Input JSON: {exc}") from exc

        thought_match = cls.THOUGHT_RE.search(cleaned)
        thought = thought_match.group("thought").strip() if thought_match else None
        return ParsedOutput(thought=thought, action=action_match.group("action"), args=args)

    @classmethod
    def parse_message(cls, message: dict[str, Any]) -> ParsedOutput:
        tool_calls = message.get("tool_calls") or []
        if tool_calls:
            first_call = tool_calls[0]
            function = first_call.get("function", {})
            name = function.get("name")
            raw_args = function.get("arguments") or "{}"
            if not name:
                raise ParseError("Missing function name in tool call")
            try:
                args = json.loads(raw_args) if isinstance(raw_args, str) else dict(raw_args)
            except (TypeError, json.JSONDecodeError) as exc:
                raise ParseError(f"Invalid function arguments JSON: {exc}") from exc
            return ParsedOutput(action=name, args=args)

        content = str(message.get("content") or "")
        return cls.parse(content)

    @staticmethod
    def _strip_code_fences(text: str) -> str:
        return re.sub(r"```(?:json|text)?\s*|\s*```", "", text.strip(), flags=re.IGNORECASE)
