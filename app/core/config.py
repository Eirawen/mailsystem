from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=(".env", ".env.example"), extra="ignore")

    app_name: str = Field(default="mailsystem", alias="APP_NAME")
    app_env: str = Field(default="development", alias="APP_ENV")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    database_url: str = Field(alias="DATABASE_URL")
    redis_url: str = Field(alias="REDIS_URL")

    default_provider: str = Field(default="smtp", alias="DEFAULT_PROVIDER")

    smtp_host: str = Field(default="localhost", alias="SMTP_HOST")
    smtp_port: int = Field(default=25, alias="SMTP_PORT")
    smtp_user: str = Field(default="", alias="SMTP_USER")
    smtp_pass: str = Field(default="", alias="SMTP_PASS")
    smtp_tls: bool = Field(default=False, alias="SMTP_TLS")

    max_retries: int = Field(default=5, alias="MAX_RETRIES")
    retry_base_seconds: int = Field(default=10, alias="RETRY_BASE_SECONDS")
    retry_max_seconds: int = Field(default=900, alias="RETRY_MAX_SECONDS")

    rate_limit_window_seconds: int = Field(default=60, alias="RATE_LIMIT_WINDOW_SECONDS")
    rate_limit_tenant_per_window: int = Field(default=300, alias="RATE_LIMIT_TENANT_PER_WINDOW")
    rate_limit_provider_per_window: int = Field(default=120, alias="RATE_LIMIT_PROVIDER_PER_WINDOW")

    webhook_replay_window_seconds: int = Field(default=300, alias="WEBHOOK_REPLAY_WINDOW_SECONDS")
    webhook_secret_smtp: str = Field(default="", alias="WEBHOOK_SECRET_SMTP")
    webhook_secret_mock: str = Field(default="", alias="WEBHOOK_SECRET_MOCK")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
