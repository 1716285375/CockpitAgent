from typing import Literal

from pydantic import BaseModel, Field

from app.tools.base import BaseTool
from app.tools.vehicle.bus import MemoryVehicleCommandBus, VehicleCommandBus


class SeatArgs(BaseModel):
    position: Literal["driver", "passenger"] = Field(default="driver", description="座椅位置")
    action: Literal["forward", "backward", "up", "down", "heat_on", "heat_off"] = Field(description="座椅动作")
    level: int | None = Field(default=None, ge=1, le=3, description="加热档位")


class SeatControlTool(BaseTool):
    name = "seat_control"
    description = "控制座椅前后、高低与加热开关"
    args_schema = SeatArgs

    def __init__(self, bus: VehicleCommandBus | None = None):
        self.bus = bus or MemoryVehicleCommandBus()

    async def execute(self, position: str, action: str, level: int | None = None) -> dict:
        result = await self.bus.send(
            "SEAT_SET",
            {"position": position, "action": action, "level": level},
        )
        return result.as_dict()
