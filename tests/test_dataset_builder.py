import asyncio
from datetime import datetime, timezone

from app.ml.dataset_builder import DatasetBuilder
from app.schemas.features import FeatureRow, FeaturesResponse


class StubFeatureService:
    async def build_features(self, symbol: str, lookback: int | None):
        return FeaturesResponse(
            symbol=symbol,
            window_used=lookback or 3,
            upstream_latest_timestamp=datetime(2024, 1, 3, tzinfo=timezone.utc),
            features=[
                FeatureRow(
                    timestamp=datetime(2024, 1, 1, tzinfo=timezone.utc),
                    close=100,
                    simple_return=0.0,
                    moving_average=100,
                    rolling_volatility=0.0,
                ),
                FeatureRow(
                    timestamp=datetime(2024, 1, 2, tzinfo=timezone.utc),
                    close=110,
                    simple_return=0.1,
                    moving_average=105,
                    rolling_volatility=0.02,
                ),
                FeatureRow(
                    timestamp=datetime(2024, 1, 3, tzinfo=timezone.utc),
                    close=120,
                    simple_return=0.0909,
                    moving_average=115,
                    rolling_volatility=0.03,
                ),
            ],
        )


def test_dataset_builder_creates_labeled_rows() -> None:
    builder = DatasetBuilder(feature_service=StubFeatureService())
    result = asyncio.run(builder.build(symbols=["AAPL"], lookback=3))

    assert result.summary["rows"] == 2
    assert "target_next_return" in result.dataset.columns
    assert list(result.dataset["symbol"].unique()) == ["AAPL"]
