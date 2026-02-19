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
    request_id: str
    latency_ms: float


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
