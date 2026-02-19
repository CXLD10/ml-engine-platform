import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.api.middleware import RateLimitMiddleware
from app.api.routes.admin import router as admin_router
from app.api.routes.features import router as features_router
from app.api.routes.health import router as health_router
from app.api.routes.models import router as models_router
from app.api.routes.monitoring import router as monitoring_router
from app.api.routes.predict import router as predict_router
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.exceptions import ServiceError
from app.schemas.error import ErrorResponse

settings = get_settings()
configure_logging(settings.resolved_log_level)
logger = logging.getLogger(__name__)

app = FastAPI(title=settings.app_name)
app.add_middleware(
    RateLimitMiddleware,
    max_requests=settings.rate_limit_requests,
    window_seconds=settings.rate_limit_window_seconds,
)
app.include_router(health_router)
# Expose feature routes with and without prefix for downstream compatibility.
app.include_router(features_router)
app.include_router(features_router, prefix=settings.api_prefix)

# Phase 2 APIs
app.include_router(predict_router)
app.include_router(models_router)
app.include_router(monitoring_router)
app.include_router(admin_router)
app.include_router(predict_router, prefix=settings.api_prefix)
app.include_router(models_router, prefix=settings.api_prefix)
app.include_router(monitoring_router, prefix=settings.api_prefix)
app.include_router(admin_router, prefix=settings.api_prefix)


@app.exception_handler(ServiceError)
async def service_error_handler(_: Request, exc: ServiceError) -> JSONResponse:
    logger.error(
        "service_error",
        extra={"error": exc.error, "details": exc.details, "status": exc.status_code},
    )
    payload = ErrorResponse(error=exc.error, details=exc.details, status=exc.status_code)
    return JSONResponse(status_code=exc.status_code, content=payload.model_dump())


@app.exception_handler(Exception)
async def unhandled_error_handler(_: Request, exc: Exception) -> JSONResponse:
    logger.exception("unhandled_error", extra={"error": str(exc)})
    payload = ErrorResponse(error="internal_error", details="Unexpected server error", status=500)
    return JSONResponse(status_code=500, content=payload.model_dump())
