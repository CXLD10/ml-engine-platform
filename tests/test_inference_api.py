from datetime import datetime, timezone

from fastapi.testclient import TestClient

from app.api.dependencies import get_inference_engine
from app.main import app


class StubInferenceEngine:
    async def predict(self, symbol: str, lookback: int | None = None, version: str | None = None):
        return {
            "symbol": symbol,
            "prediction": 0.73,
            "confidence": 0.82,
            "model_version": version or "v1",
            "features": {
                "close": 102.0,
                "simple_return": 0.01,
                "moving_average": 101.5,
                "rolling_volatility": 0.02,
            },
            "timestamp": datetime(2024, 1, 1, tzinfo=timezone.utc).isoformat(),
        }


def test_predict_response_schema() -> None:
    app.dependency_overrides[get_inference_engine] = lambda: StubInferenceEngine()
    try:
        client = TestClient(app)
        response = client.get("/predict", params={"symbol": "AAPL"})
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    body = response.json()
    assert body["symbol"] == "AAPL"
    assert "prediction" in body
    assert "confidence" in body
    assert "model_version" in body
    assert "features" in body
    assert "timestamp" in body
