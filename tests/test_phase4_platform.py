import asyncio
import os
from pathlib import Path

import numpy as np
from fastapi.testclient import TestClient

from app.api.dependencies import get_audit_logger, get_inference_engine, get_model_registry, get_training_manager
from app.core.config import Settings
from app.logging.audit import PredictionAuditLogger
from app.main import app
from app.ml.modeling import LinearRegressor
from app.ml.registry import ModelRegistry


class StubBatchInferenceEngine:
    async def predict(self, symbol: str, lookback: int | None = None, version: str | None = None):
        if symbol == "MSFT":
            raise RuntimeError("upstream unavailable")
        return {
            "symbol": symbol,
            "prediction": 0.55,
            "confidence": 0.77,
            "model_version": version or "v3",
        }


class StubTrainingManager:
    def __init__(self) -> None:
        self._status = {
            "state": "idle",
            "started_at": None,
            "completed_at": None,
            "latest_version": None,
            "error": None,
        }

    def start_training(self) -> dict:
        self._status.update({"state": "running", "started_at": "2024-01-01T00:00:00+00:00"})
        self._status.update({"state": "succeeded", "completed_at": "2024-01-01T00:01:00+00:00", "latest_version": "v9"})
        return {"status": "started", "training": self._status}

    def status(self) -> dict:
        return self._status


def _build_registry(tmp_path: Path) -> ModelRegistry:
    registry = ModelRegistry(root_dir=str(tmp_path / "models"))
    model = LinearRegressor().fit(np.array([[1.0], [2.0]]), np.array([0.2, 0.3]))
    registry.save_model_package(
        version="v1",
        model=model,
        metadata={"version": "v1", "trained_at": "2024-01-01T00:00:00+00:00", "training_feature_stats": {}},
        metrics={"rmse": 0.2},
        feature_columns=["f1"],
        dataset_summary={"rows": 2},
    )
    return registry


def test_batch_prediction_partial_failures() -> None:
    app.dependency_overrides[get_inference_engine] = lambda: StubBatchInferenceEngine()
    try:
        client = TestClient(app)
        response = client.post("/predict/batch", json={"symbols": ["AAPL", "MSFT"]})
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    items = response.json()["items"]
    assert items[0]["symbol"] == "AAPL"
    assert items[0]["version"] == "v3"
    assert items[1]["symbol"] == "MSFT"
    assert "error" in items[1]


def test_admin_api_requires_key(tmp_path: Path) -> None:
    manager = StubTrainingManager()
    app.dependency_overrides[get_training_manager] = lambda: manager
    try:
        client = TestClient(app)
        unauthorized = client.post("/admin/train")
        assert unauthorized.status_code == 401

        authorized = client.post("/admin/train", headers={"X-API-Key": "changeme-admin-key"})
        assert authorized.status_code == 200
    finally:
        app.dependency_overrides.clear()


def test_async_training_status_flow(tmp_path: Path) -> None:
    manager = StubTrainingManager()
    app.dependency_overrides[get_training_manager] = lambda: manager
    try:
        client = TestClient(app)
        start = client.post("/admin/train", headers={"X-API-Key": "changeme-admin-key"})
        assert start.status_code == 200

        status = client.get("/admin/train/status", headers={"X-API-Key": "changeme-admin-key"})
        assert status.status_code == 200
        assert status.json()["training"]["state"] == "succeeded"
        assert status.json()["training"]["latest_version"] == "v9"
    finally:
        app.dependency_overrides.clear()


def test_config_profile_switching() -> None:
    os.environ["MARKET_DATA_BASE_URL"] = "https://example.com"
    dev = Settings(ENV="development")
    staging = Settings(ENV="staging")
    prod = Settings(ENV="production")

    assert dev.resolved_log_level == "DEBUG"
    assert staging.resolved_log_level == "INFO"
    assert prod.resolved_log_level == "WARNING"


def test_admin_audit_clear(tmp_path: Path) -> None:
    audit_logger = PredictionAuditLogger(log_file=str(tmp_path / "audit.log"), limit=10)
    audit_logger.log_prediction(model_version="v1", features={"close": 1.0}, prediction=0.5, latency_ms=2.0)
    app.dependency_overrides[get_audit_logger] = lambda: audit_logger
    try:
        client = TestClient(app)
        response = client.delete("/admin/audit/clear", headers={"X-API-Key": "changeme-admin-key"})
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert audit_logger.get_recent() == []
