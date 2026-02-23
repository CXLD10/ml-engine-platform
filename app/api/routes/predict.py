from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.dependencies import get_audit_logger, get_inference_engine
from app.logging.audit import PredictionAuditLogger
from app.ml.inference import InferenceEngine
from app.schemas.error import ErrorResponse
from app.schemas.ml import (
    BatchPredictRequest,
    BatchPredictResponse,
    BatchPredictionItem,
    PredictResponse,
    PredictionAuditResponse,
)

router = APIRouter(tags=["inference"])


def _legacy_prediction_to_label(prediction: Any) -> str:
    if isinstance(prediction, str) and prediction in {"BUY", "HOLD", "SELL"}:
        return prediction
    value = float(prediction)
    if value > 0.55:
        return "BUY"
    if value < 0.45:
        return "SELL"
    return "HOLD"


def _normalize_predict_payload(payload: dict[str, Any], exchange: str) -> dict[str, Any]:
    if "probability_up" in payload and "inference_latency_ms" in payload:
        return payload

    confidence = float(payload.get("confidence", 0.0))
    prediction_raw = payload.get("prediction", "HOLD")
    prediction_label = _legacy_prediction_to_label(prediction_raw)

    if isinstance(prediction_raw, (int, float)):
        probability_up = max(0.0, min(1.0, float(prediction_raw)))
    else:
        probability_up = {"BUY": 0.7, "HOLD": 0.5, "SELL": 0.3}[prediction_label]

    return {
        "exchange": payload.get("exchange", exchange),
        "symbol": payload.get("symbol"),
        "prediction": prediction_label,
        "confidence": confidence,
        "probability_up": probability_up,
        "probability_down": 1.0 - probability_up,
        "risk_score": 0.0,
        "expected_return": 0.0,
        "forecast_horizon": payload.get("forecast_horizon", "5d"),
        "model_version": payload.get("model_version") or payload.get("version", "unknown"),
        "degraded_input": bool(payload.get("degraded_input", False)),
        "input_data_status": payload.get("input_data_status", "degraded" if payload.get("degraded_input") else "healthy"),
        "inference_latency_ms": float(payload.get("inference_latency_ms", payload.get("latency_ms", 0.0))),
        "timestamp": payload.get("timestamp", datetime.now(timezone.utc).isoformat()),
        "request_id": payload.get("request_id", "legacy"),
        "features": payload.get("features"),
        "latency_ms": float(payload.get("latency_ms", payload.get("inference_latency_ms", 0.0))),
    }


async def _predict_with_compat(engine: InferenceEngine, symbol: str, exchange: str, version: str | None) -> dict[str, Any]:
    try:
        return await engine.predict(symbol=symbol, exchange=exchange, version=version)
    except TypeError as exc:
        if "unexpected keyword argument 'exchange'" not in str(exc):
            raise
        return await engine.predict(symbol=symbol, version=version)


@router.get(
    "/predict",
    response_model=PredictResponse,
    responses={404: {"model": ErrorResponse}, 422: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
)
async def predict(
    symbol: str = Query(min_length=1),
    exchange: str = Query(default="NASDAQ"),
    version: str | None = Query(default=None),
    engine: InferenceEngine = Depends(get_inference_engine),
) -> PredictResponse:
    try:
        payload = await _predict_with_compat(engine=engine, symbol=symbol.upper(), exchange=exchange.upper(), version=version)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    normalized = _normalize_predict_payload(payload=payload, exchange=exchange.upper())
    return PredictResponse.model_validate(normalized)


@router.post("/predict/batch", response_model=BatchPredictResponse)
async def predict_batch(
    request: BatchPredictRequest,
    version: str | None = Query(default=None),
    engine: InferenceEngine = Depends(get_inference_engine),
) -> BatchPredictResponse:
    results: list[BatchPredictionItem] = []
    for symbol in request.symbols:
        try:
            payload = await _predict_with_compat(engine=engine, symbol=symbol.upper(), exchange="NASDAQ", version=version)
            results.append(
                BatchPredictionItem(
                    symbol=symbol.upper(),
                    prediction=_legacy_prediction_to_label(payload.get("prediction", "HOLD")),
                    confidence=payload.get("confidence"),
                    version=payload.get("model_version") or payload.get("version"),
                )
            )
        except Exception as exc:
            results.append(BatchPredictionItem(symbol=symbol.upper(), error=str(exc)))
    return BatchPredictResponse(items=results)


@router.get("/predictions/recent", response_model=PredictionAuditResponse)
async def recent_predictions(
    limit: int = Query(default=20, ge=1),
    audit_logger: PredictionAuditLogger = Depends(get_audit_logger),
) -> PredictionAuditResponse:
    return PredictionAuditResponse(entries=audit_logger.get_recent(limit=limit))
