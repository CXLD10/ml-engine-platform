from __future__ import annotations

import re
from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

SCHEMA_VERSION = "1.1"
KNOWN_EXCHANGES = {"NSE", "BSE", "NASDAQ"}
SYMBOL_REGEX = re.compile(r"^[A-Z][A-Z0-9._-]{0,19}$")


class Exchange(str, Enum):
    NSE = "NSE"
    BSE = "BSE"
    NASDAQ = "NASDAQ"


class DataSource(str, Enum):
    LIVE = "live"
    CACHE = "cache"


class P1ErrorResponse(BaseModel):
    schema_version: str
    status: str
    error_code: str
    message: str
    exchange: str


class P1BaseResponse(BaseModel):
    model_config = ConfigDict(extra="allow")

    schema_version: str
    status: str = "ok"
    exchange: Exchange
    symbol: str | None = None
    data_source: DataSource | None = None
    exchange_status: str | None = None

    @field_validator("schema_version")
    @classmethod
    def validate_schema(cls, value: str) -> str:
        if value != SCHEMA_VERSION:
            raise ValueError(f"Unsupported schema_version={value}")
        return value

    @field_validator("symbol")
    @classmethod
    def validate_symbol(cls, value: str | None) -> str | None:
        if value is None:
            return value
        normalized = value.upper().strip()
        if not SYMBOL_REGEX.match(normalized):
            raise ValueError("symbol format is invalid")
        return normalized


class QuoteResponse(P1BaseResponse):
    symbol: str
    price: float = Field(gt=0)
    open: float | None = Field(default=None, gt=0)
    high: float | None = Field(default=None, gt=0)
    low: float | None = Field(default=None, gt=0)
    previous_close: float | None = Field(default=None, gt=0)
    volume: int | None = Field(default=None, ge=0)
    currency: str
    timestamp: datetime

    @field_validator("timestamp")
    @classmethod
    def to_utc(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            raise ValueError("timestamp must be timezone-aware")
        return value.astimezone(timezone.utc)


class Candle(BaseModel):
    timestamp: datetime
    open: float = Field(gt=0)
    high: float = Field(gt=0)
    low: float = Field(gt=0)
    close: float = Field(gt=0)
    volume: int = Field(gt=0)

    @field_validator("timestamp")
    @classmethod
    def to_utc(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            raise ValueError("timestamp must be timezone-aware")
        return value.astimezone(timezone.utc)

    @model_validator(mode="after")
    def check_ohlc(self) -> "Candle":
        if self.high < max(self.open, self.close, self.low):
            raise ValueError("invalid high for OHLC candle")
        if self.low > min(self.open, self.close, self.high):
            raise ValueError("invalid low for OHLC candle")
        return self


class CandleResponse(P1BaseResponse):
    symbol: str
    interval: str
    candles: list[Candle]

    @field_validator("candles")
    @classmethod
    def check_monotonic(cls, candles: list[Candle]) -> list[Candle]:
        for idx in range(1, len(candles)):
            if candles[idx].timestamp <= candles[idx - 1].timestamp:
                raise ValueError("candles must have strictly ascending timestamps")
            prev_close = candles[idx - 1].close
            if prev_close > 0 and abs(candles[idx].close - prev_close) / prev_close > 0.5:
                raise ValueError("candle close jump exceeds 50% single-step threshold")
        return candles


class FundamentalsPayload(BaseModel):
    market_cap: float
    pe_ratio: float
    pb_ratio: float | None = None
    forward_pe: float
    eps: float
    revenue: float
    revenue_growth: float
    ebitda: float
    net_income: float
    debt_to_equity: float
    roe: float
    sector: str
    industry: str
    country: str
    currency: str


class FundamentalsResponse(P1BaseResponse):
    symbol: str
    fundamentals: FundamentalsPayload


class CompanyResponse(P1BaseResponse):
    symbol: str
    company_name: str
    sector: str
    industry: str
    description: str | None = None
    website: str | None = None
    market_cap: float | None = Field(default=None, ge=0)


class MarketStatusResponse(P1BaseResponse):
    is_open: bool
    session: str
    timezone: str
    server_time_utc: datetime
    local_exchange_time: datetime

    @field_validator("server_time_utc", "local_exchange_time")
    @classmethod
    def validate_timestamps(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            raise ValueError("timestamp must be timezone-aware")
        return value.astimezone(timezone.utc)
