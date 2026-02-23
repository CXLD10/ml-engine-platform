from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class PredictResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    exchange: str
    symbol: str
    prediction: Literal["BUY", "HOLD", "SELL"]
    confidence: float
    probability_up: float
    probability_down: float
    risk_score: float
    expected_return: float
    forecast_horizon: str = "5d"
    model_version: str
    degraded_input: bool = False
    input_data_status: str | None = None
    inference_latency_ms: float
    timestamp: datetime
    request_id: str
    features: dict[str, float] | None = None
    latency_ms: float | None = None


class ModelRecord(BaseModel):
    version: str
    created_at: datetime | None = None
    training_metrics: dict[str, float]
    validation_metrics: dict[str, float]
    dataset_window: dict[str, Any]
    is_active: bool


class ModelSummaryResponse(BaseModel):
    available_versions: list[str]
    active_version: str | None
    models: list[ModelRecord] = []


class ModelDetailsResponse(BaseModel):
    version: str
    metadata: dict[str, Any]
    metrics: dict[str, float]
    feature_columns: list[str]
    dataset_summary: dict[str, Any]
    created_at: datetime | None = None
    training_metrics: dict[str, float] = {}
    validation_metrics: dict[str, float] = {}
    dataset_window: dict[str, Any] = {}
    is_active: bool


class PredictionAuditResponse(BaseModel):
    entries: list[dict[str, Any]]


class DriftStatusResponse(BaseModel):
    status: str
    details: dict[str, Any]


class MonitoringHistoryResponse(BaseModel):
    runs: list[dict[str, Any]]


class FreshnessResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    upstream_last_seen: str | None
    model_last_trained: str | None
    last_prediction_time: str | None


class LatencyResponse(BaseModel):
    avg_latency_ms: float
    recent_calls: int


class BatchPredictRequest(BaseModel):
    symbols: list[str] = Field(min_length=1)


class BatchPredictionItem(BaseModel):
    symbol: str
    prediction: Literal["BUY", "HOLD", "SELL"] | None = None
    confidence: float | None = None
    version: str | None = None
    error: str | None = None


class BatchPredictResponse(BaseModel):
    items: list[BatchPredictionItem]
