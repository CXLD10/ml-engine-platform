from functools import lru_cache

from pydantic import Field, HttpUrl
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = Field(default="ml-feature-platform", alias="APP_NAME")
    app_env: str = Field(default="local", alias="APP_ENV")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    api_prefix: str = Field(default="/api/v1", alias="API_PREFIX")

    market_data_base_url: HttpUrl = Field(alias="MARKET_DATA_BASE_URL")
    market_data_timeout_seconds: float = Field(default=5.0, alias="MARKET_DATA_TIMEOUT_SECONDS")
    market_data_retry_attempts: int = Field(default=3, alias="MARKET_DATA_RETRY_ATTEMPTS")
    market_data_retry_backoff_seconds: float = Field(default=0.5, alias="MARKET_DATA_RETRY_BACKOFF_SECONDS")
    market_data_candle_interval: str = Field(default="1m", alias="MARKET_DATA_CANDLE_INTERVAL")

    default_lookback: int = Field(default=100, alias="DEFAULT_LOOKBACK")
    max_lookback: int = Field(default=1000, alias="MAX_LOOKBACK")
    ma_window: int = Field(default=14, alias="MA_WINDOW")
    vol_window: int = Field(default=14, alias="VOL_WINDOW")


@lru_cache
def get_settings() -> Settings:
    return Settings()
