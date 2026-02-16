from datetime import datetime

from pydantic import BaseModel, Field


class FeatureRow(BaseModel):
    timestamp: datetime
    close: float
    simple_return: float
    moving_average: float
    rolling_volatility: float


class FeaturesResponse(BaseModel):
    symbol: str
    window_used: int = Field(ge=1)
    upstream_latest_timestamp: datetime
    features: list[FeatureRow]
