from pydantic import BaseModel, Field

from app.tools.base import BaseTool


class WeatherArgs(BaseModel):
    city: str = Field(default="上海", min_length=1, description="城市名称")


class WeatherTool(BaseTool):
    name = "weather"
    description = "查询指定城市的天气"
    args_schema = WeatherArgs

    async def execute(self, city: str = "上海") -> dict:
        return {
            "status": "ok",
            "city": city,
            "condition": "晴",
            "temperature": 26,
            "unit": "celsius",
            "suggestion": "适合通勤, 注意防晒",
        }

