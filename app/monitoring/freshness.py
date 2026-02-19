from __future__ import annotations

from datetime import datetime, timezone


class FreshnessTracker:
    def __init__(self) -> None:
        self._upstream_last_seen: str | None = None
        self._model_last_trained: str | None = None
        self._last_prediction_time: str | None = None

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()

    def record_upstream_seen(self) -> None:
        self._upstream_last_seen = self._now()

    def record_model_trained(self, timestamp: str | None = None) -> None:
        self._model_last_trained = timestamp or self._now()

    def record_prediction(self, timestamp: str | None = None) -> None:
        self._last_prediction_time = timestamp or self._now()

    def snapshot(self) -> dict[str, str | None]:
        return {
            "upstream_last_seen": self._upstream_last_seen,
            "model_last_trained": self._model_last_trained,
            "last_prediction_time": self._last_prediction_time,
        }
