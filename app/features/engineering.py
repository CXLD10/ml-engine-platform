from __future__ import annotations

import pandas as pd

from app.exceptions import DataValidationError
from app.schemas.features import FeatureRow
from app.schemas.p1 import Candle, FundamentalsPayload


def compute_features(candles: list[Candle], ma_window: int, vol_window: int, fundamentals: FundamentalsPayload | None = None) -> list[FeatureRow]:
    frame = pd.DataFrame([c.model_dump() for c in candles])
    frame = frame.sort_values("timestamp", kind="mergesort").reset_index(drop=True)

    frame["simple_return"] = frame["close"].pct_change().fillna(0.0)
    frame["moving_average"] = frame["close"].rolling(window=ma_window, min_periods=1).mean()
    frame["rolling_volatility"] = frame["close"].pct_change().rolling(window=vol_window, min_periods=1).std().fillna(0.0)
    frame["return_5d"] = frame["close"].pct_change(periods=5).fillna(0.0)
    frame["zscore_20"] = ((frame["close"] - frame["close"].rolling(20, min_periods=1).mean()) / frame["close"].rolling(20, min_periods=1).std().replace(0, 1)).fillna(0.0)
    running_max = frame["close"].cummax().replace(0, 1)
    frame["drawdown"] = ((frame["close"] / running_max) - 1.0).fillna(0.0)

    pe = fundamentals.pe_ratio if fundamentals else None
    pb = fundamentals.pb_ratio if fundamentals else None
    mcap = fundamentals.market_cap if fundamentals else None
    frame["fund_pe_ratio"] = pe if pe is not None else 0.0
    frame["fund_pb_ratio"] = pb if pb is not None else 0.0
    frame["fund_market_cap"] = mcap if mcap is not None else 0.0

    completeness = 1.0 - (frame.isna().sum().sum() / max(frame.size, 1))
    if completeness < 0.98:
        raise DataValidationError(
            error="feature_completeness_below_threshold",
            details={"required": 0.98, "actual": float(completeness)},
            status_code=422,
        )

    feature_rows: list[FeatureRow] = []
    for row in frame.fillna(0.0).itertuples(index=False):
        feature_rows.append(
            FeatureRow(
                timestamp=row.timestamp,
                close=float(row.close),
                simple_return=float(row.simple_return),
                moving_average=float(row.moving_average),
                rolling_volatility=float(row.rolling_volatility),
                return_5d=float(row.return_5d),
                zscore_20=float(row.zscore_20),
                drawdown=float(row.drawdown),
                fund_pe_ratio=float(row.fund_pe_ratio),
                fund_pb_ratio=float(row.fund_pb_ratio),
                fund_market_cap=float(row.fund_market_cap),
            )
        )

    return feature_rows
