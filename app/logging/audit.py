from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class PredictionAuditLogger:
    def __init__(self, log_file: str, limit: int) -> None:
        self._log_file = Path(log_file)
        self._log_file.parent.mkdir(parents=True, exist_ok=True)
        self._limit = limit

    @staticmethod
    def new_request_id() -> str:
        return str(uuid.uuid4())

    def log_prediction(
        self,
        *,
        model_version: str,
        features: dict[str, float],
        prediction: float,
        latency_ms: float,
        request_id: str | None = None,
    ) -> dict[str, Any]:
        record = {
            "request_id": request_id or self.new_request_id(),
            "model_version": model_version,
            "features": features,
            "prediction": prediction,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "latency_ms": latency_ms,
        }
        with self._log_file.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(record, default=str) + "\n")
        return record

    def get_recent(self, limit: int | None = None) -> list[dict[str, Any]]:
        resolved_limit = min(limit or self._limit, self._limit)
        if not self._log_file.exists():
            return []
        lines = self._log_file.read_text(encoding="utf-8").splitlines()
        return [json.loads(line) for line in lines[-resolved_limit:] if line.strip()]
