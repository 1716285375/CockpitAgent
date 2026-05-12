from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel


class ToolError(RuntimeError):
    pass


class EmptyArgs(BaseModel):
    pass


class BaseTool(ABC):
    name: str
    description: str
    args_schema: type[BaseModel] = EmptyArgs
    enabled: bool = True

    def schema(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.args_schema.model_json_schema(),
        }

    @abstractmethod
    async def execute(self, **kwargs: Any) -> dict[str, Any]:
        raise NotImplementedError

