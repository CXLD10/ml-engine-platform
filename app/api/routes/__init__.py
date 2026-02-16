from app.api.routes.features import router as features_router
from app.api.routes.health import router as health_router
from app.api.routes.models import router as models_router
from app.api.routes.predict import router as predict_router

__all__ = ["health_router", "features_router", "predict_router", "models_router"]
