from pathlib import Path

import numpy as np

from app.ml.modeling import LinearRegressor
from app.ml.registry import ModelRegistry


def test_registry_serialization_round_trip(tmp_path: Path) -> None:
    registry = ModelRegistry(root_dir=str(tmp_path / "models"))
    model = LinearRegressor().fit(np.array([[1.0], [2.0]]), np.array([0.1, 0.2]))

    registry.save_model_package(
        version="v1",
        model=model,
        metadata={"version": "v1"},
        metrics={"rmse": 1.0},
        feature_columns=["f1"],
        dataset_summary={"rows": 2},
    )

    loaded, metadata = registry.load_model("v1")
    assert metadata["version"] == "v1"
    pred = float(loaded.predict(np.array([[1.5]]))[0])
    assert pred > 0
