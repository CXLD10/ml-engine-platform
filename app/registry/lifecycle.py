from __future__ import annotations

import json
import pickle
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class ModelLifecycleRegistry:
    def __init__(self, root_dir: str) -> None:
        self.root_dir = Path(root_dir)
        self.root_dir.mkdir(parents=True, exist_ok=True)
        self._registry_file = self.root_dir / "registry.json"
        self._history_file = self.root_dir / "training_history.json"

    def _read_registry(self) -> dict[str, Any]:
        if not self._registry_file.exists():
            return {"active_version": None, "models": {}}
        payload = json.loads(self._registry_file.read_text())
        payload.setdefault("active_version", None)
        payload.setdefault("models", {})
        return payload

    def _write_registry(self, payload: dict[str, Any]) -> None:
        self._registry_file.write_text(json.dumps(payload, indent=2, default=str))

    def _read_history(self) -> list[dict[str, Any]]:
        if not self._history_file.exists():
            return []
        return json.loads(self._history_file.read_text())

    def _write_history(self, history: list[dict[str, Any]]) -> None:
        self._history_file.write_text(json.dumps(history, indent=2, default=str))

    def list_versions(self) -> list[str]:
        return sorted([p.name for p in self.root_dir.iterdir() if p.is_dir() and p.name.startswith("v")])

    def list_models(self) -> list[dict[str, Any]]:
        registry = self._read_registry()
        active = registry.get("active_version")
        items: list[dict[str, Any]] = []
        for version in self.list_versions():
            model_record = registry["models"].get(version, {})
            items.append(
                {
                    "version": version,
                    "created_at": model_record.get("created_at"),
                    "training_metrics": model_record.get("training_metrics", {}),
                    "validation_metrics": model_record.get("validation_metrics", {}),
                    "dataset_window": model_record.get("dataset_window", {}),
                    "is_active": version == active,
                }
            )
        return items

    def get_active_version(self) -> str | None:
        return self._read_registry().get("active_version")

    def activate_version(self, version: str) -> None:
        if not (self.root_dir / version).exists():
            raise FileNotFoundError(f"Model version {version} not found")
        registry = self._read_registry()
        if version not in registry["models"]:
            raise FileNotFoundError(f"Model metadata for version {version} not found")
        registry["active_version"] = version
        self._write_registry(registry)

    def set_active_version(self, version: str) -> None:
        self.activate_version(version)

    def rollback(self, version: str) -> None:
        self.activate_version(version)

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

        created_at = metadata.get("trained_at", datetime.now(timezone.utc).isoformat())
        training_metrics = metadata.get("training_metrics", {})
        validation_metrics = metadata.get("validation_metrics", metrics)
        dataset_window = metadata.get("dataset_window", dataset_summary)

        registry = self._read_registry()
        registry["models"][version] = {
            "created_at": created_at,
            "training_metrics": training_metrics,
            "validation_metrics": validation_metrics,
            "dataset_window": dataset_window,
        }
        registry["active_version"] = version
        self._write_registry(registry)

        history = self._read_history()
        history.append(
            {
                "version": version,
                "training_metrics": training_metrics,
                "validation_metrics": validation_metrics,
                "dataset_range": dataset_window,
                "timestamp": created_at,
            }
        )
        self._write_history(history)

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

        registry = self._read_registry()
        model_record = registry["models"].get(version, {})

        return {
            "version": version,
            "metadata": json.loads((version_dir / "metadata.json").read_text()),
            "metrics": json.loads((version_dir / "metrics.json").read_text()),
            "feature_columns": json.loads((version_dir / "feature_columns.json").read_text()),
            "dataset_summary": json.loads((version_dir / "dataset_summary.json").read_text()),
            "created_at": model_record.get("created_at"),
            "training_metrics": model_record.get("training_metrics", {}),
            "validation_metrics": model_record.get("validation_metrics", {}),
            "dataset_window": model_record.get("dataset_window", {}),
            "is_active": version == registry.get("active_version"),
        }

    def get_training_history(self) -> list[dict[str, Any]]:
        return self._read_history()

    def get_training_feature_stats(self, version: str | None = None) -> dict[str, dict[str, float]]:
        _, metadata = self.load_model(version=version)
        return metadata.get("training_feature_stats", {})
