from datetime import datetime

from pydantic import BaseModel, Field


class Candle(BaseModel):
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float


class CandleResponse(BaseModel):
    symbol: str = Field(min_length=1)
    interval: str = Field(default="1m")
    candles: list[Candle]
