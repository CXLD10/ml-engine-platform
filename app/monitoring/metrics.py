from __future__ import annotations

from collections import deque


class LatencyTracker:
    def __init__(self, max_samples: int = 200) -> None:
        self._samples: deque[float] = deque(maxlen=max_samples)

    def record(self, latency_ms: float) -> None:
        self._samples.append(latency_ms)

    def snapshot(self) -> dict[str, float | int]:
        if not self._samples:
            return {"avg_latency_ms": 0.0, "recent_calls": 0}
        avg = sum(self._samples) / len(self._samples)
        return {"avg_latency_ms": round(avg, 4), "recent_calls": len(self._samples)}
