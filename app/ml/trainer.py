from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

import numpy as np

from app.ml.dataset_builder import DatasetBuilder, FEATURE_COLUMNS
from app.ml.modeling import LinearRegressor
from app.ml.registry import ModelRegistry


@dataclass
class TrainingConfig:
    symbols: list[str]
    lookback: int
    test_size: float
    random_state: int
    cv_folds: int
    model_params: dict[str, int | float | str]


class Trainer:
    def __init__(self, dataset_builder: DatasetBuilder, registry: ModelRegistry) -> None:
        self._dataset_builder = dataset_builder
        self._registry = registry

    async def train(self, config: TrainingConfig, version: str | None = None) -> dict[str, str | dict]:
        build_result = await self._dataset_builder.build(symbols=config.symbols, lookback=config.lookback)
        dataset = build_result.dataset
        if dataset.empty:
            raise ValueError("Dataset is empty; cannot train model")

        x = dataset[FEATURE_COLUMNS].to_numpy()
        y = dataset["target_next_return"].to_numpy()

        rng = np.random.default_rng(config.random_state)
        indices = np.arange(len(x))
        rng.shuffle(indices)

        split_idx = int(len(indices) * (1 - config.test_size))
        train_idx, val_idx = indices[:split_idx], indices[split_idx:]

        x_train, y_train = x[train_idx], y[train_idx]
        x_val, y_val = x[val_idx], y[val_idx]

        model = LinearRegressor(
            fit_intercept=bool(config.model_params.get("fit_intercept", True)),
            l2_alpha=float(config.model_params.get("l2_alpha", 1e-6)),
        )
        model.fit(x_train, y_train)
        predictions = model.predict(x_val)

        metrics = {
            "rmse": float(np.sqrt(np.mean((y_val - predictions) ** 2))),
            "r2": float(1 - (np.sum((y_val - predictions) ** 2) / np.sum((y_val - y_val.mean()) ** 2))),
        }

        if config.cv_folds > 1:
            folds = np.array_split(indices, config.cv_folds)
            fold_rmse: list[float] = []
            for fold in folds:
                train_fold = np.setdiff1d(indices, fold)
                model_cv = LinearRegressor(
                    fit_intercept=bool(config.model_params.get("fit_intercept", True)),
                    l2_alpha=float(config.model_params.get("l2_alpha", 1e-6)),
                )
                model_cv.fit(x[train_fold], y[train_fold])
                fold_pred = model_cv.predict(x[fold])
                fold_rmse.append(float(np.sqrt(np.mean((y[fold] - fold_pred) ** 2))))
            metrics["cv_rmse_mean"] = float(np.mean(fold_rmse))

        resolved_version = version or self._registry.next_version()
        metadata = {
            "version": resolved_version,
            "trained_at": datetime.now(timezone.utc).isoformat(),
            "algorithm": "LinearRegressor",
            "lookback": config.lookback,
            "symbols": config.symbols,
            "test_size": config.test_size,
            "cv_folds": config.cv_folds,
            "model_params": config.model_params,
        }
        self._registry.save_model_package(
            version=resolved_version,
            model=model,
            metadata=metadata,
            metrics=metrics,
            feature_columns=FEATURE_COLUMNS,
            dataset_summary=build_result.summary,
        )

        return {"version": resolved_version, "metrics": metrics, "dataset_summary": build_result.summary}
