from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.dependencies import get_inference_engine
from app.ml.inference import InferenceEngine
from app.schemas.error import ErrorResponse
from app.schemas.ml import PredictResponse

router = APIRouter(tags=["inference"])


@router.get(
    "/predict",
    response_model=PredictResponse,
    responses={404: {"model": ErrorResponse}, 422: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
)
async def predict(
    symbol: str = Query(min_length=1),
    version: str | None = Query(default=None),
    engine: InferenceEngine = Depends(get_inference_engine),
) -> PredictResponse:
    try:
        payload = await engine.predict(symbol=symbol.upper(), version=version)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return PredictResponse.model_validate(payload)
