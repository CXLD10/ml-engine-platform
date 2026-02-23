import asyncio
from datetime import datetime, timedelta, timezone

import pytest

from app.clients.market_data import MarketDataClient
from app.core.config import Settings
from app.exceptions import DataValidationError
from app.ml.inference import InferenceEngine
from app.schemas.p1 import SCHEMA_VERSION


def _settings() -> Settings:
    return Settings(MARKET_DATA_BASE_URL="https://example.com", MARKET_DATA_RETRY_ATTEMPTS=1, MARKET_DATA_TIMEOUT_SECONDS=0.1)


def _candle(ts: datetime, close: float = 100.0):
    return {"timestamp": ts.isoformat(), "open": close, "high": close + 1, "low": close - 1, "close": close, "volume": 1000}


def test_schema_version_mismatch_rejected(monkeypatch):
    client = MarketDataClient(_settings())

    async def fake_get(path, params):
        return {
            "schema_version": "9.9",
            "status": "ok",
            "exchange": "NASDAQ",
            "symbol": "AAPL",
            "interval": "1d",
            "candles": [_candle(datetime.now(timezone.utc))],
        }

    monkeypatch.setattr(client, "_get_with_retry", fake_get)

    with pytest.raises(DataValidationError):
        asyncio.run(client.get_candles("AAPL", lookback=1))


def test_candle_validation_non_monotonic(monkeypatch):
    client = MarketDataClient(_settings())
    now = datetime.now(timezone.utc)

    async def fake_get(path, params):
        return {
            "schema_version": SCHEMA_VERSION,
            "status": "ok",
            "exchange": "NASDAQ",
            "symbol": "AAPL",
            "interval": "1d",
            "candles": [_candle(now), _candle(now)],
        }

    monkeypatch.setattr(client, "_get_with_retry", fake_get)

    with pytest.raises(DataValidationError):
        asyncio.run(client.get_historical("AAPL", "NASDAQ", now - timedelta(days=2), now))


def test_degraded_flag_propagation(monkeypatch):
    client = MarketDataClient(_settings())

    async def fake_get(path, params):
        if path == "/historical":
            now = datetime.now(timezone.utc)
            return {
                "schema_version": SCHEMA_VERSION,
                "status": "ok",
                "exchange": "NASDAQ",
                "data_source": "cache",
                "exchange_status": "degraded",
                "symbol": "AAPL",
                "interval": "1d",
                "candles": [_candle(now - timedelta(days=2)), _candle(now - timedelta(days=1))],
            }
        if path == "/fundamentals":
            return {
                "schema_version": SCHEMA_VERSION,
                "status": "ok",
                "exchange": "NASDAQ",
                "symbol": "AAPL",
                "fundamentals": {"market_cap": 1000.0, "pe_ratio": 10.0, "forward_pe": 9.0, "eps": 5.0, "revenue": 100.0, "revenue_growth": 0.1, "ebitda": 20.0, "net_income": 10.0, "debt_to_equity": 0.5, "roe": 0.12, "sector": "Tech", "industry": "Software", "country": "US", "currency": "USD"},
            }
        raise AssertionError(path)

    monkeypatch.setattr(client, "_get_with_retry", fake_get)

    from app.services.feature_service import FeatureService

    svc = FeatureService(client, _settings())
    out = asyncio.run(svc.build_features("AAPL", lookback=2))
    assert out.degraded_input is True


def test_inference_latency_field_present(monkeypatch):
    class DummyRegistry:
        def load_model(self, version=None):
            class M:
                def predict(self, x):
                    return [0.1]

            return M(), {"version": "v1"}

    class DummyFeatureService:
        def __init__(self):
            self._market_data_client = self

        async def get_market_status(self, exchange):
            return type("S", (), {"is_open": True})()

        async def get_quote(self, symbol, exchange):
            return type("Q", (), {"timestamp": datetime.now(timezone.utc)})()

        async def build_features(self, symbol, lookback, exchange):
            row = type("F", (), {
                "close": 1.0,
                "simple_return": 0.1,
                "moving_average": 1.0,
                "rolling_volatility": 0.1,
                "return_5d": 0.02,
                "zscore_20": 0.0,
                "drawdown": -0.01,
                "fund_pe_ratio": 10.0,
                "fund_pb_ratio": 1.0,
                "fund_market_cap": 100.0,
            })()
            return type("R", (), {"features": [row], "degraded_input": True, "upstream_latest_timestamp": datetime.now(timezone.utc)})()

    class Dummy:
        def record(self, *args, **kwargs):
            return None

        def record_upstream_seen(self, *args, **kwargs):
            return None

        def record_prediction(self, *args, **kwargs):
            return None

    class DummyAudit:
        def log_prediction(self, **kwargs):
            return {"request_id": "r1", "timestamp": datetime.now(timezone.utc).isoformat()}

    engine = InferenceEngine(DummyFeatureService(), DummyRegistry(), 10, DummyAudit(), Dummy(), Dummy(), Dummy())
    payload = asyncio.run(engine.predict("AAPL"))
    assert "inference_latency_ms" in payload
    assert payload["degraded_input"] is True
