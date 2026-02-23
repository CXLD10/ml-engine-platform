from app.registry.lifecycle import GCSModelLifecycleRegistry, ModelLifecycleRegistry


class ModelRegistry:
    def __new__(cls, root_dir: str):
        if root_dir.startswith("gs://"):
            return GCSModelLifecycleRegistry(root_uri=root_dir)
        return ModelLifecycleRegistry(root_dir=root_dir)


__all__ = ["ModelRegistry", "ModelLifecycleRegistry", "GCSModelLifecycleRegistry"]
