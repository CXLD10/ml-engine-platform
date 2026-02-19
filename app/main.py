import logging
import uuid

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
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
from app.schemas.api import ApiErrorResponse

settings = get_settings()
configure_logging(settings.resolved_log_level)
logger = logging.getLogger(__name__)

app = FastAPI(title=settings.app_name)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.resolved_cors_allow_origins,
    allow_methods=settings.resolved_cors_allow_methods,
    allow_headers=settings.resolved_cors_allow_headers,
)
app.add_middleware(
    RateLimitMiddleware,
    max_requests=settings.rate_limit_requests,
    window_seconds=settings.rate_limit_window_seconds,
)


@app.middleware("http")
async def request_context_middleware(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    request.state.request_id = request_id
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response


app.include_router(health_router)
app.include_router(features_router)
app.include_router(features_router, prefix=settings.api_prefix)
app.include_router(predict_router)
app.include_router(models_router)
app.include_router(monitoring_router)
app.include_router(admin_router)
app.include_router(predict_router, prefix=settings.api_prefix)
app.include_router(models_router, prefix=settings.api_prefix)
app.include_router(monitoring_router, prefix=settings.api_prefix)
app.include_router(admin_router, prefix=settings.api_prefix)


@app.exception_handler(ServiceError)
async def service_error_handler(request: Request, exc: ServiceError) -> JSONResponse:
    logger.error(
        "service_error",
        extra={"error": exc.error, "details": exc.details, "status": exc.status_code, "request_id": request.state.request_id},
    )
    payload = ApiErrorResponse(error=exc.error, details=exc.details, code=exc.status_code, request_id=request.state.request_id)
    return JSONResponse(status_code=exc.status_code, content=payload.model_dump())


@app.exception_handler(HTTPException)
async def http_error_handler(request: Request, exc: HTTPException) -> JSONResponse:
    payload = ApiErrorResponse(
        error="http_error",
        details=exc.detail,
        code=exc.status_code,
        request_id=request.state.request_id,
    )
    return JSONResponse(status_code=exc.status_code, content=payload.model_dump())


@app.exception_handler(Exception)
async def unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("unhandled_error", extra={"error": str(exc), "request_id": request.state.request_id})
    payload = ApiErrorResponse(
        error="internal_error", details="Unexpected server error", code=500, request_id=request.state.request_id
    )
    return JSONResponse(status_code=500, content=payload.model_dump())
