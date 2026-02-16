from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class PredictResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    symbol: str
    prediction: float
    confidence: float
    model_version: str
    features: dict[str, float]
    timestamp: datetime


class ModelSummaryResponse(BaseModel):
    available_versions: list[str]
    active_version: str | None


class ModelDetailsResponse(BaseModel):
    version: str
    metadata: dict[str, Any]
    metrics: dict[str, float]
    feature_columns: list[str]
    dataset_summary: dict[str, Any]
    is_active: bool
