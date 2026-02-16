from datetime import datetime, timezone

from app.features.engineering import compute_features
from app.schemas.upstream import Candle


def test_compute_features_deterministic_values() -> None:
    candles = [
        Candle(timestamp=datetime(2024, 1, 1, tzinfo=timezone.utc), open=100, high=101, low=99, close=100, volume=10),
        Candle(timestamp=datetime(2024, 1, 2, tzinfo=timezone.utc), open=101, high=102, low=100, close=110, volume=12),
        Candle(timestamp=datetime(2024, 1, 3, tzinfo=timezone.utc), open=111, high=112, low=110, close=121, volume=8),
    ]

    rows = compute_features(candles, ma_window=2, vol_window=2)
    assert len(rows) == 3
    assert rows[0].simple_return == 0.0
    assert round(rows[1].simple_return, 6) == 0.1
    assert round(rows[2].moving_average, 4) == 115.5
