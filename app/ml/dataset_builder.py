from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import pandas as pd

from app.schemas.features import FeaturesResponse
from app.services.feature_service import FeatureService

FEATURE_COLUMNS = ["close", "simple_return", "moving_average", "rolling_volatility"]


@dataclass
class DatasetBuildResult:
    dataset: pd.DataFrame
    summary: dict[str, int | list[str]]


class DatasetBuilder:
    def __init__(self, feature_service: FeatureService) -> None:
        self._feature_service = feature_service

    async def build(self, symbols: Iterable[str], lookback: int) -> DatasetBuildResult:
        frames: list[pd.DataFrame] = []

        for symbol in symbols:
            response: FeaturesResponse = await self._feature_service.build_features(
                symbol=symbol.upper(), lookback=lookback
            )
            frame = pd.DataFrame([item.model_dump() for item in response.features])
            if frame.empty:
                continue

            frame = frame.sort_values("timestamp", kind="mergesort").reset_index(drop=True)
            frame["symbol"] = response.symbol
            frame["target_next_return"] = frame["simple_return"].shift(-1)
            frame = frame.dropna(subset=["target_next_return"]).reset_index(drop=True)
            frames.append(frame)

        if not frames:
            empty = pd.DataFrame(columns=["symbol", "timestamp", *FEATURE_COLUMNS, "target_next_return"])
            return DatasetBuildResult(dataset=empty, summary={"rows": 0, "symbols": list(symbols)})

        dataset = pd.concat(frames, ignore_index=True)
        summary = {
            "rows": int(len(dataset)),
            "symbols": sorted(dataset["symbol"].unique().tolist()),
        }
        return DatasetBuildResult(dataset=dataset, summary=summary)
