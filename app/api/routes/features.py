from fastapi import APIRouter, Depends, Query

from app.schemas.error import ErrorResponse
from app.schemas.features import FeaturesResponse
from app.services.feature_service import FeatureService
from app.api.dependencies import get_feature_service

router = APIRouter(tags=["features"])


@router.get(
    "/features",
    response_model=FeaturesResponse,
    responses={502: {"model": ErrorResponse}, 422: {"model": ErrorResponse}},
)
async def get_features(
    symbol: str = Query(min_length=1),
    lookback: int | None = Query(default=None, ge=1),
    service: FeatureService = Depends(get_feature_service),
) -> FeaturesResponse:
    return await service.build_features(symbol=symbol.upper(), lookback=lookback)
