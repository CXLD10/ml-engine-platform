from __future__ import annotations

import time
from datetime import datetime, timezone

import numpy as np

from app.exceptions import DataValidationError
from app.logging.audit import PredictionAuditLogger
from app.ml.dataset_builder import FEATURE_COLUMNS
from app.ml.registry import ModelRegistry
from app.monitoring.drift import DriftDetector
from app.monitoring.freshness import FreshnessTracker
from app.monitoring.metrics import LatencyTracker
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

    async def predict(self, symbol: str, exchange: str = "NASDAQ", lookback: int | None = None, version: str | None = None) -> dict:
        start = time.perf_counter()
        model, metadata = self._registry.load_model(version=version)

        market_status = await self._feature_service._market_data_client.get_market_status(exchange=exchange)
        if not market_status.is_open:
            raise DataValidationError(error="EXCHANGE_UNAVAILABLE", details="Market is closed", status_code=503)

        quote = await self._feature_service._market_data_client.get_quote(symbol=symbol, exchange=exchange)
        features_response = await self._feature_service.build_features(
            symbol=symbol,
            lookback=lookback or self._default_lookback,
            exchange=exchange,
        )

        now = datetime.now(timezone.utc)
        if (now - quote.timestamp).total_seconds() > 90:
            raise DataValidationError(error="stale_quote", details="Quote timestamp too old", status_code=422)
        if (now - features_response.upstream_latest_timestamp).total_seconds() > 600:
            raise DataValidationError(error="stale_candle", details="Candle timestamp too old", status_code=422)

        latest = features_response.features[-1]
        feature_dict = {col: float(getattr(latest, col)) for col in FEATURE_COLUMNS}
        x = np.array([[feature_dict[col] for col in FEATURE_COLUMNS]])
        raw = float(model.predict(x)[0])

        probability_up = max(0.0, min(1.0, 0.5 + raw / 2.0))
        probability_down = 1.0 - probability_up
        prediction = "BUY" if probability_up > 0.55 else "SELL" if probability_up < 0.45 else "HOLD"
        confidence = abs(probability_up - 0.5) * 2
        degraded_input = features_response.degraded_input
        if degraded_input:
            confidence *= 0.7

        risk_score = float(min(1.0, max(0.0, latest.rolling_volatility * 10)))
        expected_return = float(latest.return_5d / 5.0)

        latency_ms = (time.perf_counter() - start) * 1000
        self._latency_tracker.record(latency_ms)
        self._drift_detector.record(feature_dict)
        self._freshness_tracker.record_upstream_seen()
        audit_record = self._audit_logger.log_prediction(model_version=metadata["version"], features=feature_dict, prediction=probability_up, latency_ms=latency_ms)
        self._freshness_tracker.record_prediction(audit_record["timestamp"])

        return {
            "exchange": exchange,
            "symbol": symbol,
            "prediction": prediction,
            "confidence": float(confidence),
            "probability_up": float(probability_up),
            "probability_down": float(probability_down),
            "risk_score": risk_score,
            "expected_return": expected_return,
            "forecast_horizon": "5d",
            "model_version": metadata["version"],
            "degraded_input": degraded_input,
            "input_data_status": "degraded" if degraded_input else "healthy",
            "inference_latency_ms": latency_ms,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "request_id": audit_record["request_id"],
        }
