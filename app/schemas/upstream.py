from datetime import datetime

from pydantic import AliasChoices, BaseModel, ConfigDict, Field


class Candle(BaseModel):
    model_config = ConfigDict(extra="ignore")

    timestamp: datetime = Field(
        validation_alias=AliasChoices("timestamp", "interval_start", "time", "datetime")
    )
    open: float = Field(validation_alias=AliasChoices("open", "open_price"))
    high: float = Field(validation_alias=AliasChoices("high", "high_price"))
    low: float = Field(validation_alias=AliasChoices("low", "low_price"))
    close: float = Field(validation_alias=AliasChoices("close", "close_price"))
    volume: float = Field(validation_alias=AliasChoices("volume", "volume_sum"))


class CandleResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    symbol: str = Field(min_length=1)
    interval: str = Field(default="1m")
    candles: list[Candle]
