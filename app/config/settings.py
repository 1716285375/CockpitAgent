from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Cockpit Agent"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    app_env: str = "development"

    llm_base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    llm_api_key: str = ""
    llm_model: str = "qwen-max"
    llm_timeout: float = 30.0
    llm_max_retries: int = Field(default=3, ge=1)
    llm_circuit_failure_threshold: int = Field(default=3, ge=1)
    llm_circuit_recovery_seconds: float = Field(default=30.0, ge=1.0)

    redis_url: str = "memory://"
    mysql_dsn: str = ""

    nacos_server: str = ""
    nacos_namespace: str = ""
    nacos_group: str = "DEFAULT_GROUP"
    nacos_data_id: str = "cockpit-agent"
    nacos_poll_interval_seconds: float = Field(default=5.0, ge=1.0)

    jwt_secret: str = ""
    jwt_expire_hours: int = 24
    auth_enabled: bool = False

    hmac_secret: str = ""
    signature_enabled: bool = False
    signature_window_seconds: int = Field(default=60, ge=1)

    rate_limit_enabled: bool = True
    rate_limit_requests: int = Field(default=60, ge=1)
    rate_limit_window_seconds: int = Field(default=60, ge=1)

    agent_max_steps: int = Field(default=6, ge=1, le=20)
    tool_timeout_seconds: float = Field(default=5.0, ge=0.1)
    tool_cache_ttl_seconds: float = Field(default=10.0, ge=0.0)
    context_max_tokens: int = Field(default=3000, ge=200)
    context_keep_recent: int = Field(default=4, ge=1)
    context_ttl_seconds: int = Field(default=86400, ge=60)
    session_lock_ttl_seconds: int = Field(default=60, ge=1)


@lru_cache
def get_settings() -> Settings:
    return Settings()


def safe_settings(settings: Settings | None = None) -> dict:
    settings = settings or get_settings()
    data = settings.model_dump()
    for key in ("llm_api_key", "jwt_secret", "hmac_secret", "mysql_dsn"):
        if data.get(key):
            data[key] = "***"
    return data
