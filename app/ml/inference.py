from __future__ import annotations

from datetime import datetime, timezone

import numpy as np

from app.ml.dataset_builder import FEATURE_COLUMNS
from app.ml.registry import ModelRegistry
from app.schemas.features import FeaturesResponse
from app.services.feature_service import FeatureService


class InferenceEngine:
    def __init__(self, feature_service: FeatureService, registry: ModelRegistry, default_lookback: int) -> None:
        self._feature_service = feature_service
        self._registry = registry
        self._default_lookback = default_lookback

    async def predict(self, symbol: str, lookback: int | None = None, version: str | None = None) -> dict:
        model, metadata = self._registry.load_model(version=version)
        resolved_lookback = lookback or self._default_lookback
        features_response: FeaturesResponse = await self._feature_service.build_features(symbol=symbol, lookback=resolved_lookback)
        latest = features_response.features[-1]

        feature_dict = {
            "close": latest.close,
            "simple_return": latest.simple_return,
            "moving_average": latest.moving_average,
            "rolling_volatility": latest.rolling_volatility,
        }

        x = np.array([[feature_dict[col] for col in FEATURE_COLUMNS]])
        prediction = float(model.predict(x)[0])
        confidence = max(0.0, min(1.0, 1.0 - abs(prediction)))

        return {
            "symbol": symbol,
            "prediction": prediction,
            "confidence": confidence,
            "model_version": metadata["version"],
            "features": feature_dict,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
