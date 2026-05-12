from typing import Literal

from pydantic import BaseModel, Field

from app.tools.base import BaseTool


class VehicleStatusArgs(BaseModel):
    item: Literal["battery", "fuel", "tire_pressure", "mileage", "all"] = Field(default="all")


class VehicleStatusTool(BaseTool):
    name = "vehicle_status"
    description = "查询车辆状态, 包括电量、油量、胎压和里程"
    args_schema = VehicleStatusArgs

    async def execute(self, item: str = "all") -> dict:
        status = {
            "battery": "78%",
            "fuel": "46%",
            "tire_pressure": {"front_left": 2.4, "front_right": 2.4, "rear_left": 2.5, "rear_right": 2.5},
            "mileage": "18320 km",
        }
        return {"status": "ok", "item": item, "data": status if item == "all" else status[item]}

