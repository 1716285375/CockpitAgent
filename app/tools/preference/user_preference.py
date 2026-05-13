from typing import Protocol
from urllib.parse import urlparse

from pydantic import BaseModel, Field

from app.tools.base import BaseTool, ToolError


class SetPreferenceArgs(BaseModel):
    user_id: str = Field(default="anonymous", min_length=1)
    key: str = Field(min_length=1)
    value: str = Field(min_length=1)


class GetPreferenceArgs(BaseModel):
    user_id: str = Field(default="anonymous", min_length=1)
    key: str = Field(min_length=1)


class PreferenceStore(Protocol):
    async def set(self, user_id: str, key: str, value: str) -> None:
        ...

    async def get(self, user_id: str, key: str) -> str | None:
        ...


class MemoryPreferenceStore:
    def __init__(self):
        self._data: dict[str, dict[str, str]] = {}

    async def set(self, user_id: str, key: str, value: str) -> None:
        self._data.setdefault(user_id, {})[key] = value

    async def get(self, user_id: str, key: str) -> str | None:
        return self._data.get(user_id, {}).get(key)


class MySQLPreferenceStore:
    def __init__(self, dsn: str):
        self.dsn = dsn
        self.connection_kwargs = self._parse_dsn(dsn)

    async def set(self, user_id: str, key: str, value: str) -> None:
        import aiomysql

        conn = await aiomysql.connect(**self.connection_kwargs)
        try:
            async with conn.cursor() as cursor:
                await cursor.execute(
                    """
                    INSERT INTO user_preferences (user_id, pref_key, pref_value)
                    VALUES (%s, %s, %s)
                    ON DUPLICATE KEY UPDATE pref_value = VALUES(pref_value)
                    """,
                    (user_id, key, value),
                )
                await conn.commit()
        finally:
            conn.close()

    async def get(self, user_id: str, key: str) -> str | None:
        import aiomysql

        conn = await aiomysql.connect(**self.connection_kwargs)
        try:
            async with conn.cursor() as cursor:
                await cursor.execute(
                    "SELECT pref_value FROM user_preferences WHERE user_id = %s AND pref_key = %s",
                    (user_id, key),
                )
                row = await cursor.fetchone()
                return None if row is None else str(row[0])
        finally:
            conn.close()

    @staticmethod
    def _parse_dsn(dsn: str) -> dict:
        parsed = urlparse(dsn)
        if parsed.scheme not in {"mysql", "mysql+aiomysql"}:
            raise ValueError("MYSQL_DSN must use mysql:// or mysql+aiomysql://")
        return {
            "host": parsed.hostname or "localhost",
            "port": parsed.port or 3306,
            "user": parsed.username or "",
            "password": parsed.password or "",
            "db": parsed.path.lstrip("/"),
            "autocommit": False,
        }


class SetUserPreferenceTool(BaseTool):
    name = "set_user_preference"
    description = "保存用户偏好, 如常用温度、座椅位置、导航偏好"
    args_schema = SetPreferenceArgs
    cacheable = False

    def __init__(self, store: PreferenceStore):
        self.store = store

    async def execute(self, user_id: str, key: str, value: str) -> dict:
        await self.store.set(user_id, key, value)
        return {"status": "ok", "user_id": user_id, "key": key, "value": value}


class GetUserPreferenceTool(BaseTool):
    name = "get_user_preference"
    description = "读取用户偏好"
    args_schema = GetPreferenceArgs
    cacheable = False

    def __init__(self, store: PreferenceStore):
        self.store = store

    async def execute(self, user_id: str, key: str) -> dict:
        value = await self.store.get(user_id, key)
        if value is None:
            raise ToolError(f"Preference {key} not found for user {user_id}")
        return {"status": "ok", "user_id": user_id, "key": key, "value": value}
