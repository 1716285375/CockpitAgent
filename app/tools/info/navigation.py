from pydantic import BaseModel, Field

from app.tools.base import BaseTool


class NavigationArgs(BaseModel):
    destination: str = Field(min_length=1, description="目的地或 POI")
    origin: str = Field(default="当前位置", description="起点")


class NavigationTool(BaseTool):
    name = "navigation"
    description = "查询目的地路线和预计用时"
    args_schema = NavigationArgs

    async def execute(self, destination: str, origin: str = "当前位置") -> dict:
        return {
            "status": "ok",
            "origin": origin,
            "destination": destination,
            "distance_km": 12.4,
            "eta_minutes": 28,
            "route": "推荐路线",
        }

