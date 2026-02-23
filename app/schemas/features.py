from datetime import datetime

from pydantic import BaseModel, Field


class FeatureRow(BaseModel):
    timestamp: datetime
    close: float
    simple_return: float
    moving_average: float
    rolling_volatility: float
    return_5d: float = 0.0
    zscore_20: float = 0.0
    drawdown: float = 0.0
    fund_pe_ratio: float = 0.0
    fund_pb_ratio: float = 0.0
    fund_market_cap: float = 0.0


class FeaturesResponse(BaseModel):
    symbol: str
    window_used: int = Field(ge=1)
    upstream_latest_timestamp: datetime
    degraded_input: bool = False
    features: list[FeatureRow]
