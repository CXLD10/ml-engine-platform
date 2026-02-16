from __future__ import annotations

import argparse
import asyncio
from pathlib import Path

import yaml

from app.clients.market_data import MarketDataClient
from app.core.config import get_settings
from app.ml.dataset_builder import DatasetBuilder
from app.ml.registry import ModelRegistry
from app.ml.trainer import Trainer, TrainingConfig
from app.services.feature_service import FeatureService


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train a versioned ML model")
    parser.add_argument("--config", type=str, default="configs/train.yaml")
    parser.add_argument("--version", type=str, default=None)
    return parser.parse_args()


async def run(config_path: str, version: str | None = None) -> None:
    settings = get_settings()
    payload = yaml.safe_load(Path(config_path).read_text())

    config = TrainingConfig(
        symbols=payload["symbols"],
        lookback=int(payload["lookback"]),
        test_size=float(payload["test_size"]),
        random_state=int(payload["random_state"]),
        cv_folds=int(payload.get("cv_folds", 1)),
        model_params=payload.get("model_params", {}),
    )

    feature_service = FeatureService(
        market_data_client=MarketDataClient(settings=settings),
        settings=settings,
    )
    trainer = Trainer(
        dataset_builder=DatasetBuilder(feature_service=feature_service),
        registry=ModelRegistry(root_dir=settings.model_registry_dir),
    )

    result = await trainer.train(config=config, version=version)
    print(result)


if __name__ == "__main__":
    args = parse_args()
    asyncio.run(run(config_path=args.config, version=args.version))
