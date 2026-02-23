from functools import lru_cache
from typing import Literal

from pydantic import Field, HttpUrl
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore", protected_namespaces=("settings_",))

    app_name: str = Field(default="ml-engine-platform", alias="APP_NAME")
    env: Literal["development", "staging", "production"] = Field(default="development", alias="ENV")
    app_env: str = Field(default="local", alias="APP_ENV")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    api_prefix: str = Field(default="/api/v1", alias="API_PREFIX")
    cors_allow_origins: str = Field(default="*", alias="CORS_ALLOW_ORIGINS")
    cors_allow_methods: str = Field(default="*", alias="CORS_ALLOW_METHODS")
    cors_allow_headers: str = Field(default="*", alias="CORS_ALLOW_HEADERS")

    market_data_base_url: HttpUrl = Field(alias="MARKET_DATA_BASE_URL")
    market_data_timeout_seconds: float = Field(default=5.0, alias="MARKET_DATA_TIMEOUT_SECONDS")
    market_data_retry_attempts: int = Field(default=3, alias="MARKET_DATA_RETRY_ATTEMPTS")
    market_data_retry_backoff_seconds: float = Field(default=0.5, alias="MARKET_DATA_RETRY_BACKOFF_SECONDS")
    market_data_candle_interval: str = Field(default="1m", alias="MARKET_DATA_CANDLE_INTERVAL")

    default_lookback: int = Field(default=100, alias="DEFAULT_LOOKBACK")
    max_lookback: int = Field(default=1000, alias="MAX_LOOKBACK")
    ma_window: int = Field(default=14, alias="MA_WINDOW")
    vol_window: int = Field(default=14, alias="VOL_WINDOW")

    model_registry_dir: str = Field(default="artifacts/models", alias="MODEL_REGISTRY_DIR")
    inference_lookback: int = Field(default=120, alias="INFERENCE_LOOKBACK")
    drift_threshold: float = Field(default=0.25, alias="DRIFT_THRESHOLD")
    audit_log_limit: int = Field(default=100, alias="AUDIT_LOG_LIMIT")
    audit_log_file: str = Field(default="artifacts/predictions/audit.log", alias="AUDIT_LOG_FILE")
    admin_api_key: str = Field(default="changeme-admin-key", alias="ADMIN_API_KEY")
    train_symbols: str = Field(default="AAPL,MSFT", alias="TRAIN_SYMBOLS")
    train_lookback: int = Field(default=252, alias="TRAIN_LOOKBACK")
    train_test_size: float = Field(default=0.2, alias="TRAIN_TEST_SIZE")
    train_random_state: int = Field(default=42, alias="TRAIN_RANDOM_STATE")
    train_cv_folds: int = Field(default=3, alias="TRAIN_CV_FOLDS")
    rate_limit_requests: int = Field(default=120, alias="RATE_LIMIT_REQUESTS")
    rate_limit_window_seconds: int = Field(default=60, alias="RATE_LIMIT_WINDOW_SECONDS")

    @property
    def resolved_log_level(self) -> str:
        if self.log_level and self.log_level.upper() != "INFO":
            return self.log_level.upper()
        if self.env == "development":
            return "DEBUG"
        if self.env == "staging":
            return "INFO"
        return "WARNING"

    @property
    def resolved_train_symbols(self) -> list[str]:
        return [symbol.strip().upper() for symbol in self.train_symbols.split(",") if symbol.strip()]

    @property
    def resolved_cors_allow_origins(self) -> list[str]:
        if self.cors_allow_origins.strip() == "*":
            return ["*"]
        return [item.strip() for item in self.cors_allow_origins.split(",") if item.strip()]

    @property
    def resolved_cors_allow_methods(self) -> list[str]:
        if self.cors_allow_methods.strip() == "*":
            return ["*"]
        return [item.strip().upper() for item in self.cors_allow_methods.split(",") if item.strip()]

    @property
    def resolved_cors_allow_headers(self) -> list[str]:
        if self.cors_allow_headers.strip() == "*":
            return ["*"]
        return [item.strip() for item in self.cors_allow_headers.split(",") if item.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
