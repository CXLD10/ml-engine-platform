from pathlib import Path

from fastapi import APIRouter, Request

from app.core.config import get_settings
from app.schemas.api import ApiResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=ApiResponse[dict[str, str]])
async def health_check(request: Request) -> ApiResponse[dict[str, str]]:
    settings = get_settings()
    return ApiResponse(
        data={"status": "ok", "service": settings.app_name, "environment": settings.env},
        request_id=getattr(request.state, "request_id", None),
    )


@router.get("/ready", response_model=ApiResponse[dict[str, str]])
async def readiness_check(request: Request) -> ApiResponse[dict[str, str]]:
    settings = get_settings()
    registry_path = Path(settings.model_registry_dir)
    status = "ok" if registry_path.exists() else "degraded"
    return ApiResponse(
        data={"status": status, "registry_path": str(registry_path)},
        message="Readiness checks completed",
        request_id=getattr(request.state, "request_id", None),
    )
