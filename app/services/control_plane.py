from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any

from app.core.config import Settings
from app.ml.trainer import Trainer, TrainingConfig

logger = logging.getLogger(__name__)


class AsyncTrainingManager:
    def __init__(self, trainer: Trainer, settings: Settings) -> None:
        self._trainer = trainer
        self._settings = settings
        self._task: asyncio.Task | None = None
        self._status: dict[str, Any] = {
            "state": "idle",
            "started_at": None,
            "completed_at": None,
            "latest_version": None,
            "error": None,
        }

    def start_training(self) -> dict[str, Any]:
        if self._task and not self._task.done():
            return {"status": "already_running", "training": self.status()}

        self._status.update(
            {
                "state": "running",
                "started_at": datetime.now(timezone.utc).isoformat(),
                "completed_at": None,
                "error": None,
            }
        )
        self._task = asyncio.create_task(self._run_training())
        return {"status": "started", "training": self.status()}

    async def _run_training(self) -> None:
        logger.info("training_started", extra={"symbols": self._settings.resolved_train_symbols})
        config = TrainingConfig(
            symbols=self._settings.resolved_train_symbols,
            lookback=self._settings.train_lookback,
            test_size=self._settings.train_test_size,
            random_state=self._settings.train_random_state,
            cv_folds=self._settings.train_cv_folds,
            model_params={"fit_intercept": True, "l2_alpha": 1e-6},
        )
        try:
            result = await self._trainer.train(config=config)
            self._status.update(
                {
                    "state": "succeeded",
                    "completed_at": datetime.now(timezone.utc).isoformat(),
                    "latest_version": result["version"],
                    "error": None,
                }
            )
            logger.info("training_succeeded", extra={"version": result["version"], "metrics": result["metrics"]})
        except Exception as exc:
            self._status.update(
                {
                    "state": "failed",
                    "completed_at": datetime.now(timezone.utc).isoformat(),
                    "error": str(exc),
                }
            )
            logger.exception("training_failed")

    def status(self) -> dict[str, Any]:
        return dict(self._status)
