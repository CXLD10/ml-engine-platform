import asyncio

import pytest

from app.clients.market_data import MarketDataClient
from app.core.config import Settings


def test_get_candles_raises_for_insufficient_data(monkeypatch) -> None:
    settings = Settings(
        MARKET_DATA_BASE_URL="https://example.com",
        MARKET_DATA_RETRY_ATTEMPTS=1,
        MARKET_DATA_TIMEOUT_SECONDS=0.1,
    )
    client = MarketDataClient(settings=settings)

    async def fake_get_with_retry(path, params):
        return {
            "symbol": "AAPL",
            "interval": "1m",
            "candles": [
                {
                    "timestamp": "2024-01-01T00:00:00Z",
                    "open": 100,
                    "high": 101,
                    "low": 99,
                    "close": 100,
                    "volume": 1,
                }
            ],
        }

    monkeypatch.setattr(client, "_get_with_retry", fake_get_with_retry)

    with pytest.raises(Exception) as exc:
        asyncio.run(client.get_candles(symbol="AAPL", lookback=10))
    assert getattr(exc.value, "error", None) == "insufficient_upstream_data"
