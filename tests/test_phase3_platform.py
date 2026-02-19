from __future__ import annotations

from pathlib import Path

import numpy as np
from fastapi.testclient import TestClient

from app.api.dependencies import (
    get_audit_logger,
    get_drift_detector,
    get_freshness_tracker,
    get_latency_tracker,
    get_model_registry,
)
from app.logging.audit import PredictionAuditLogger
from app.main import app
from app.ml.modeling import LinearRegressor
from app.ml.registry import ModelRegistry
from app.monitoring.drift import DriftDetector
from app.monitoring.freshness import FreshnessTracker
from app.monitoring.metrics import LatencyTracker


def _build_registry(tmp_path: Path) -> ModelRegistry:
    registry = ModelRegistry(root_dir=str(tmp_path / "models"))
    model = LinearRegressor().fit(np.array([[1.0], [2.0]]), np.array([0.2, 0.3]))
    registry.save_model_package(
        version="v1",
        model=model,
        metadata={
            "version": "v1",
            "trained_at": "2024-01-01T00:00:00+00:00",
            "training_metrics": {"rmse": 0.1},
            "validation_metrics": {"rmse": 0.2},
            "dataset_window": {"start": "2024-01-01", "end": "2024-01-02"},
            "training_feature_stats": {
                "close": {"mean": 10.0, "std": 1.0},
                "simple_return": {"mean": 0.01, "std": 0.01},
                "moving_average": {"mean": 9.8, "std": 1.0},
                "rolling_volatility": {"mean": 0.02, "std": 0.01},
            },
        },
        metrics={"rmse": 0.2},
        feature_columns=["f1"],
        dataset_summary={"rows": 2},
    )
    return registry


def test_model_activation_logic(tmp_path: Path) -> None:
    registry = _build_registry(tmp_path)
    model = LinearRegressor().fit(np.array([[1.0], [3.0]]), np.array([0.1, 0.4]))
    registry.save_model_package(
        version="v2",
        model=model,
        metadata={"version": "v2", "trained_at": "2024-01-02T00:00:00+00:00", "training_feature_stats": {}},
        metrics={"rmse": 0.3},
        feature_columns=["f1"],
        dataset_summary={"rows": 2},
    )
    assert registry.get_active_version() == "v2"
    registry.activate_version("v1")
    assert registry.get_active_version() == "v1"


def test_drift_detection_thresholds() -> None:
    detector = DriftDetector(threshold=0.2, window_size=5)
    baseline = {"close": {"mean": 10.0, "std": 0.1}}
    for value in [10.1, 9.9, 10.0, 10.2]:
        detector.record({"close": value})
    healthy = detector.evaluate(baseline)
    assert healthy["status"] == "healthy"

    for value in [20.0, 21.0, 19.5, 20.5]:
        detector.record({"close": value})
    drifted = detector.evaluate(baseline)
    assert drifted["status"] == "drift_detected"


def test_prediction_audit_logging(tmp_path: Path) -> None:
    logger = PredictionAuditLogger(log_file=str(tmp_path / "audit.log"), limit=10)
    record = logger.log_prediction(
        model_version="v1",
        features={"close": 10.0},
        prediction=0.4,
        latency_ms=5.5,
    )
    assert record["request_id"]
    assert logger.get_recent(limit=1)[0]["model_version"] == "v1"


def test_monitoring_endpoints_and_metadata_integrity(tmp_path: Path) -> None:
    registry = _build_registry(tmp_path)
    audit_logger = PredictionAuditLogger(log_file=str(tmp_path / "audit.log"), limit=20)
    drift_detector = DriftDetector(threshold=0.2, window_size=10)
    freshness_tracker = FreshnessTracker()
    latency_tracker = LatencyTracker()

    for _ in range(3):
        latency_tracker.record(10.0)
    freshness_tracker.record_prediction("2024-01-03T00:00:00+00:00")
    drift_detector.record({"close": 10.0, "simple_return": 0.01, "moving_average": 10.0, "rolling_volatility": 0.02})

    app.dependency_overrides[get_model_registry] = lambda: registry
    app.dependency_overrides[get_audit_logger] = lambda: audit_logger
    app.dependency_overrides[get_drift_detector] = lambda: drift_detector
    app.dependency_overrides[get_freshness_tracker] = lambda: freshness_tracker
    app.dependency_overrides[get_latency_tracker] = lambda: latency_tracker

    try:
        client = TestClient(app)
        models_response = client.get("/models")
        assert models_response.status_code == 200
        assert models_response.json()["models"][0]["created_at"] == "2024-01-01T00:00:00Z"

        activate_response = client.post("/models/activate/v1")
        assert activate_response.status_code == 200

        drift_response = client.get("/monitoring/drift")
        assert drift_response.status_code == 200
        assert drift_response.json()["status"] in {"healthy", "drift_detected"}

        history_response = client.get("/monitoring/history")
        assert history_response.status_code == 200
        assert len(history_response.json()["runs"]) == 1

        freshness_response = client.get("/monitoring/freshness")
        assert freshness_response.status_code == 200
        assert freshness_response.json()["model_last_trained"] == "2024-01-01T00:00:00+00:00"

        latency_response = client.get("/monitoring/latency")
        assert latency_response.status_code == 200
        assert latency_response.json()["recent_calls"] == 3

        audit_logger.log_prediction(model_version="v1", features={"close": 1.0}, prediction=0.1, latency_ms=2.0)
        recent_predictions = client.get("/predictions/recent", params={"limit": 1})
        assert recent_predictions.status_code == 200
        assert len(recent_predictions.json()["entries"]) == 1
    finally:
        app.dependency_overrides.clear()
