import pandas as pd

from app.schemas.features import FeatureRow
from app.schemas.upstream import Candle


def compute_features(candles: list[Candle], ma_window: int, vol_window: int) -> list[FeatureRow]:
    frame = pd.DataFrame([c.model_dump() for c in candles])
    frame = frame.sort_values("timestamp", kind="mergesort").reset_index(drop=True)

    frame["simple_return"] = frame["close"].pct_change().fillna(0.0)
    frame["moving_average"] = (
        frame["close"].rolling(window=ma_window, min_periods=1).mean()
    )
    frame["rolling_volatility"] = (
        frame["close"].pct_change().rolling(window=vol_window, min_periods=1).std().fillna(0.0)
    )

    feature_rows: list[FeatureRow] = []
    for row in frame.itertuples(index=False):
        feature_rows.append(
            FeatureRow(
                timestamp=row.timestamp,
                close=float(row.close),
                simple_return=float(row.simple_return),
                moving_average=float(row.moving_average),
                rolling_volatility=float(row.rolling_volatility),
            )
        )

    return feature_rows
