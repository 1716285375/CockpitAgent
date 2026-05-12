from typing import Literal

from pydantic import BaseModel, Field

from app.tools.base import BaseTool


class WindowArgs(BaseModel):
    window: Literal["driver", "passenger", "rear_left", "rear_right", "all"] = Field(default="all")
    action: Literal["open", "close", "stop"] = Field(description="车窗动作")
    percent: int | None = Field(default=None, ge=0, le=100, description="目标开度百分比")


class WindowControlTool(BaseTool):
    name = "window_control"
    description = "控制车窗升降、停止或指定开度"
    args_schema = WindowArgs

    async def execute(self, window: str, action: str, percent: int | None = None) -> dict:
        return {"status": "ok", "window": window, "action": action, "percent": percent}

