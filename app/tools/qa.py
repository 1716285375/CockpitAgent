from pydantic import BaseModel, Field

from app.tools.base import BaseTool


class VehicleQAArgs(BaseModel):
    question: str = Field(min_length=1, description="车辆功能相关问题")


class VehicleQATool(BaseTool):
    name = "vehicle_qa"
    description = "回答车辆功能、使用说明和故障提示相关问题"
    args_schema = VehicleQAArgs

    async def execute(self, question: str) -> dict:
        return {
            "status": "ok",
            "question": question,
            "answer": "请参考车辆用户手册；当前 MVP 返回本地知识占位答案。",
        }

