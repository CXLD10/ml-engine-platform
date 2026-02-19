from __future__ import annotations

import math
from collections import defaultdict, deque


class DriftDetector:
    def __init__(self, threshold: float, window_size: int = 100) -> None:
        self._threshold = threshold
        self._window_size = window_size
        self._recent: dict[str, deque[float]] = defaultdict(lambda: deque(maxlen=self._window_size))

    def record(self, features: dict[str, float]) -> None:
        for key, value in features.items():
            self._recent[key].append(float(value))

    @staticmethod
    def _stats(values: list[float]) -> tuple[float, float]:
        if not values:
            return 0.0, 0.0
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        return mean, math.sqrt(variance)

    def evaluate(self, baseline_stats: dict[str, dict[str, float]]) -> dict[str, object]:
        details: dict[str, dict[str, float | bool]] = {}
        drifted = False

        for feature, baseline in baseline_stats.items():
            recent_values = list(self._recent.get(feature, []))
            recent_mean, recent_std = self._stats(recent_values)
            baseline_mean = float(baseline.get("mean", 0.0))
            baseline_std = float(baseline.get("std", 0.0))

            mean_delta = abs(recent_mean - baseline_mean)
            std_delta = abs(recent_std - baseline_std)

            mean_ratio = mean_delta / max(abs(baseline_mean), 1e-9)
            std_ratio = std_delta / max(abs(baseline_std), 1e-9)
            feature_drift = mean_ratio > self._threshold or std_ratio > self._threshold
            drifted = drifted or feature_drift

            details[feature] = {
                "baseline_mean": baseline_mean,
                "baseline_std": baseline_std,
                "recent_mean": recent_mean,
                "recent_std": recent_std,
                "mean_deviation_ratio": mean_ratio,
                "std_deviation_ratio": std_ratio,
                "drift": feature_drift,
                "samples": len(recent_values),
            }

        return {"status": "drift_detected" if drifted else "healthy", "details": details}
