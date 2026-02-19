from fastapi import APIRouter, Depends

from app.api.dependencies import (
    get_drift_detector,
    get_freshness_tracker,
    get_latency_tracker,
    get_model_registry,
)
from app.ml.registry import ModelRegistry
from app.monitoring.drift import DriftDetector
from app.monitoring.freshness import FreshnessTracker
from app.monitoring.metrics import LatencyTracker
from app.schemas.ml import (
    DriftStatusResponse,
    FreshnessResponse,
    LatencyResponse,
    MonitoringHistoryResponse,
)

router = APIRouter(tags=["monitoring"])


@router.get("/monitoring/drift", response_model=DriftStatusResponse)
async def drift_status(
    registry: ModelRegistry = Depends(get_model_registry),
    detector: DriftDetector = Depends(get_drift_detector),
) -> DriftStatusResponse:
    baseline = registry.get_training_feature_stats()
    return DriftStatusResponse.model_validate(detector.evaluate(baseline))


@router.get("/monitoring/history", response_model=MonitoringHistoryResponse)
async def history(registry: ModelRegistry = Depends(get_model_registry)) -> MonitoringHistoryResponse:
    return MonitoringHistoryResponse(runs=registry.get_training_history())


@router.get("/monitoring/freshness", response_model=FreshnessResponse)
async def freshness(
    registry: ModelRegistry = Depends(get_model_registry),
    tracker: FreshnessTracker = Depends(get_freshness_tracker),
) -> FreshnessResponse:
    payload = tracker.snapshot()
    if payload["model_last_trained"] is None:
        history = registry.get_training_history()
        if history:
            payload["model_last_trained"] = history[-1].get("timestamp")
    return FreshnessResponse.model_validate(payload)


@router.get("/monitoring/latency", response_model=LatencyResponse)
async def latency(tracker: LatencyTracker = Depends(get_latency_tracker)) -> LatencyResponse:
    return LatencyResponse.model_validate(tracker.snapshot())
