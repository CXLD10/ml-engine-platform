from __future__ import annotations

import time
from datetime import datetime, timezone

import numpy as np

from app.logging.audit import PredictionAuditLogger
from app.ml.dataset_builder import FEATURE_COLUMNS
from app.ml.registry import ModelRegistry
from app.monitoring.drift import DriftDetector
from app.monitoring.freshness import FreshnessTracker
from app.monitoring.metrics import LatencyTracker
from app.schemas.features import FeaturesResponse
from app.services.feature_service import FeatureService


class InferenceEngine:
    def __init__(
        self,
        feature_service: FeatureService,
        registry: ModelRegistry,
        default_lookback: int,
        audit_logger: PredictionAuditLogger,
        latency_tracker: LatencyTracker,
        freshness_tracker: FreshnessTracker,
        drift_detector: DriftDetector,
    ) -> None:
        self._feature_service = feature_service
        self._registry = registry
        self._default_lookback = default_lookback
        self._audit_logger = audit_logger
        self._latency_tracker = latency_tracker
        self._freshness_tracker = freshness_tracker
        self._drift_detector = drift_detector

    async def predict(self, symbol: str, lookback: int | None = None, version: str | None = None) -> dict:
        start = time.perf_counter()
        model, metadata = self._registry.load_model(version=version)
        resolved_lookback = lookback or self._default_lookback
        features_response: FeaturesResponse = await self._feature_service.build_features(symbol=symbol, lookback=resolved_lookback)
        self._freshness_tracker.record_upstream_seen()
        latest = features_response.features[-1]

        feature_dict = {
            "close": latest.close,
            "simple_return": latest.simple_return,
            "moving_average": latest.moving_average,
            "rolling_volatility": latest.rolling_volatility,
        }

        x = np.array([[feature_dict[col] for col in FEATURE_COLUMNS]])
        prediction = float(model.predict(x)[0])
        confidence = max(0.0, min(1.0, 1.0 - abs(prediction)))

        latency_ms = (time.perf_counter() - start) * 1000
        self._latency_tracker.record(latency_ms)
        self._drift_detector.record(feature_dict)

        audit_record = self._audit_logger.log_prediction(
            model_version=metadata["version"],
            features=feature_dict,
            prediction=prediction,
            latency_ms=latency_ms,
        )
        self._freshness_tracker.record_prediction(audit_record["timestamp"])

        return {
            "symbol": symbol,
            "prediction": prediction,
            "confidence": confidence,
            "model_version": metadata["version"],
            "features": feature_dict,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "request_id": audit_record["request_id"],
            "latency_ms": latency_ms,
        }
