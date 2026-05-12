from typing import Literal

from pydantic import BaseModel, Field

from app.tools.base import BaseTool


class ACArgs(BaseModel):
    temperature: int = Field(default=22, ge=16, le=32, description="目标温度, 16-32 摄氏度")
    mode: Literal["cool", "heat", "auto"] = Field(default="auto", description="空调模式")
    fan_level: int = Field(default=2, ge=1, le=5, description="风量档位, 1-5")


class ACControlTool(BaseTool):
    name = "ac_control"
    description = "控制车辆空调, 可设定温度、模式和风量"
    args_schema = ACArgs

    async def execute(self, temperature: int, mode: str = "auto", fan_level: int = 2) -> dict:
        return {
            "status": "ok",
            "command": "AC_SET",
            "current_temp": temperature,
            "mode": mode,
            "fan_level": fan_level,
        }

