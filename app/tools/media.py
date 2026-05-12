from typing import Literal

from pydantic import BaseModel, Field

from app.tools.base import BaseTool


class PlayMusicArgs(BaseModel):
    action: Literal["play", "pause", "next", "previous"] = Field(default="play")
    query: str | None = Field(default=None, description="歌曲、歌手或歌单")


class PlayMusicTool(BaseTool):
    name = "play_music"
    description = "控制音乐播放或按关键词播放音乐"
    args_schema = PlayMusicArgs

    async def execute(self, action: str = "play", query: str | None = None) -> dict:
        return {"status": "ok", "action": action, "query": query}

