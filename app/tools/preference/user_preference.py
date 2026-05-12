from pydantic import BaseModel, Field

from app.tools.base import BaseTool, ToolError


class SetPreferenceArgs(BaseModel):
    user_id: str = Field(default="anonymous", min_length=1)
    key: str = Field(min_length=1)
    value: str = Field(min_length=1)


class GetPreferenceArgs(BaseModel):
    user_id: str = Field(default="anonymous", min_length=1)
    key: str = Field(min_length=1)


class PreferenceStore:
    def __init__(self):
        self._data: dict[str, dict[str, str]] = {}

    def set(self, user_id: str, key: str, value: str) -> None:
        self._data.setdefault(user_id, {})[key] = value

    def get(self, user_id: str, key: str) -> str | None:
        return self._data.get(user_id, {}).get(key)


class SetUserPreferenceTool(BaseTool):
    name = "set_user_preference"
    description = "保存用户偏好, 如常用温度、座椅位置、导航偏好"
    args_schema = SetPreferenceArgs

    def __init__(self, store: PreferenceStore):
        self.store = store

    async def execute(self, user_id: str, key: str, value: str) -> dict:
        self.store.set(user_id, key, value)
        return {"status": "ok", "user_id": user_id, "key": key, "value": value}


class GetUserPreferenceTool(BaseTool):
    name = "get_user_preference"
    description = "读取用户偏好"
    args_schema = GetPreferenceArgs

    def __init__(self, store: PreferenceStore):
        self.store = store

    async def execute(self, user_id: str, key: str) -> dict:
        value = self.store.get(user_id, key)
        if value is None:
            raise ToolError(f"Preference {key} not found for user {user_id}")
        return {"status": "ok", "user_id": user_id, "key": key, "value": value}

