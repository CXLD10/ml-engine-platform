from __future__ import annotations

import json
import pickle
from pathlib import Path
from typing import Any


class ModelRegistry:
    def __init__(self, root_dir: str) -> None:
        self.root_dir = Path(root_dir)
        self.root_dir.mkdir(parents=True, exist_ok=True)
        self._registry_file = self.root_dir / "registry.json"

    def list_versions(self) -> list[str]:
        return sorted([p.name for p in self.root_dir.iterdir() if p.is_dir() and p.name.startswith("v")])

    def get_active_version(self) -> str | None:
        if not self._registry_file.exists():
            return None
        payload = json.loads(self._registry_file.read_text())
        return payload.get("active_version")

    def set_active_version(self, version: str) -> None:
        self._registry_file.write_text(json.dumps({"active_version": version}, indent=2))

    def next_version(self) -> str:
        versions = self.list_versions()
        if not versions:
            return "v1"
        latest = max(int(v.removeprefix("v")) for v in versions)
        return f"v{latest + 1}"

    def save_model_package(
        self,
        version: str,
        model: Any,
        metadata: dict[str, Any],
        metrics: dict[str, float],
        feature_columns: list[str],
        dataset_summary: dict[str, Any],
    ) -> Path:
        version_dir = self.root_dir / version
        version_dir.mkdir(parents=True, exist_ok=False)

        model_path = version_dir / "model.pkl"
        with model_path.open("wb") as fh:
            pickle.dump(model, fh)
        (version_dir / "metadata.json").write_text(json.dumps(metadata, indent=2, default=str))
        (version_dir / "metrics.json").write_text(json.dumps(metrics, indent=2, default=str))
        (version_dir / "feature_columns.json").write_text(json.dumps(feature_columns, indent=2))
        (version_dir / "dataset_summary.json").write_text(json.dumps(dataset_summary, indent=2, default=str))

        self.set_active_version(version)
        return version_dir

    def load_model(self, version: str | None = None) -> tuple[Any, dict[str, Any]]:
        resolved = version or self.get_active_version()
        if not resolved:
            raise FileNotFoundError("No active model version is registered")
        version_dir = self.root_dir / resolved
        with (version_dir / "model.pkl").open("rb") as fh:
            model = pickle.load(fh)
        metadata = json.loads((version_dir / "metadata.json").read_text())
        return model, metadata

    def get_model_details(self, version: str) -> dict[str, Any]:
        version_dir = self.root_dir / version
        if not version_dir.exists():
            raise FileNotFoundError(f"Model version {version} not found")

        return {
            "version": version,
            "metadata": json.loads((version_dir / "metadata.json").read_text()),
            "metrics": json.loads((version_dir / "metrics.json").read_text()),
            "feature_columns": json.loads((version_dir / "feature_columns.json").read_text()),
            "dataset_summary": json.loads((version_dir / "dataset_summary.json").read_text()),
            "is_active": version == self.get_active_version(),
        }
