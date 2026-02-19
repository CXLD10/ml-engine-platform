from fastapi import APIRouter, Depends, HTTPException

from app.api.dependencies import get_model_registry
from app.ml.registry import ModelRegistry
from app.schemas.error import ErrorResponse
from app.schemas.ml import ModelDetailsResponse, ModelSummaryResponse

router = APIRouter(tags=["models"])


@router.get("/models", response_model=ModelSummaryResponse)
async def list_models(registry: ModelRegistry = Depends(get_model_registry)) -> ModelSummaryResponse:
    return ModelSummaryResponse(
        available_versions=registry.list_versions(),
        active_version=registry.get_active_version(),
        models=registry.list_models(),
    )


@router.get(
    "/models/{version}",
    response_model=ModelDetailsResponse,
    responses={404: {"model": ErrorResponse}},
)
async def get_model(version: str, registry: ModelRegistry = Depends(get_model_registry)) -> ModelDetailsResponse:
    try:
        details = registry.get_model_details(version)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return ModelDetailsResponse.model_validate(details)


@router.get(
    "/model/{version}",
    response_model=ModelDetailsResponse,
    responses={404: {"model": ErrorResponse}},
)
async def get_model_legacy(version: str, registry: ModelRegistry = Depends(get_model_registry)) -> ModelDetailsResponse:
    return await get_model(version=version, registry=registry)


@router.post("/models/activate/{version}", responses={404: {"model": ErrorResponse}})
async def activate_model(version: str, registry: ModelRegistry = Depends(get_model_registry)) -> dict[str, str]:
    try:
        registry.activate_version(version)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"status": "ok", "active_version": version}
