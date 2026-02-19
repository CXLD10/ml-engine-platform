from functools import lru_cache

from app.clients.market_data import MarketDataClient
from app.core.config import Settings, get_settings
from app.logging.audit import PredictionAuditLogger
from app.ml.inference import InferenceEngine
from app.ml.registry import ModelRegistry
from app.monitoring.drift import DriftDetector
from app.monitoring.freshness import FreshnessTracker
from app.monitoring.metrics import LatencyTracker
from app.services.feature_service import FeatureService


@lru_cache
def _get_market_data_client() -> MarketDataClient:
    settings: Settings = get_settings()
    return MarketDataClient(settings=settings)


@lru_cache
def get_feature_service() -> FeatureService:
    settings: Settings = get_settings()
    return FeatureService(
        market_data_client=_get_market_data_client(),
        settings=settings,
    )


@lru_cache
def get_model_registry() -> ModelRegistry:
    settings: Settings = get_settings()
    return ModelRegistry(root_dir=settings.model_registry_dir)


@lru_cache
def get_audit_logger() -> PredictionAuditLogger:
    settings = get_settings()
    return PredictionAuditLogger(log_file=settings.audit_log_file, limit=settings.audit_log_limit)


@lru_cache
def get_latency_tracker() -> LatencyTracker:
    return LatencyTracker()


@lru_cache
def get_freshness_tracker() -> FreshnessTracker:
    return FreshnessTracker()


@lru_cache
def get_drift_detector() -> DriftDetector:
    settings = get_settings()
    return DriftDetector(threshold=settings.drift_threshold)


@lru_cache
def get_inference_engine() -> InferenceEngine:
    settings = get_settings()
    return InferenceEngine(
        feature_service=get_feature_service(),
        registry=get_model_registry(),
        default_lookback=settings.inference_lookback,
        audit_logger=get_audit_logger(),
        latency_tracker=get_latency_tracker(),
        freshness_tracker=get_freshness_tracker(),
        drift_detector=get_drift_detector(),
    )
