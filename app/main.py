import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.api.routes.features import router as features_router
from app.api.routes.health import router as health_router
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.exceptions import DataValidationError, UpstreamServiceError
from app.schemas.error import ErrorResponse

settings = get_settings()
configure_logging(settings.log_level)
logger = logging.getLogger(__name__)

app = FastAPI(title=settings.app_name)
app.include_router(health_router)
app.include_router(features_router, prefix=settings.api_prefix)


@app.exception_handler(UpstreamServiceError)
async def upstream_error_handler(_: Request, exc: UpstreamServiceError) -> JSONResponse:
    logger.error("upstream_error", extra={"error": exc.message})
    payload = ErrorResponse(detail="Upstream market data service unavailable")
    return JSONResponse(status_code=502, content=payload.model_dump())


@app.exception_handler(DataValidationError)
async def data_validation_error_handler(_: Request, exc: DataValidationError) -> JSONResponse:
    logger.error("data_validation_error", extra={"error": exc.message})
    payload = ErrorResponse(detail=exc.message)
    return JSONResponse(status_code=422, content=payload.model_dump())
