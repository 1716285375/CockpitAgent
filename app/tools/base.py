from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel


class ToolError(RuntimeError):
    code = "tool_error"

    def __init__(self, message: str, code: str | None = None):
        super().__init__(message)
        if code is not None:
            self.code = code


class UnknownToolError(ToolError):
    code = "unknown_tool"


class DisabledToolError(ToolError):
    code = "disabled_tool"


class ToolValidationError(ToolError):
    code = "validation_error"


class ToolTimeoutError(ToolError):
    code = "timeout"


class EmptyArgs(BaseModel):
    pass


class BaseTool(ABC):
    name: str
    description: str
    args_schema: type[BaseModel] = EmptyArgs
    enabled: bool = True
    cacheable: bool = True

    def schema(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.args_schema.model_json_schema(),
        }

    def openai_tool_schema(self) -> dict[str, Any]:
        return {"type": "function", "function": self.schema()}

    @abstractmethod
    async def execute(self, **kwargs: Any) -> dict[str, Any]:
        raise NotImplementedError
