import asyncio
import logging
from collections.abc import Mapping
from datetime import datetime, timedelta, timezone
from typing import Any

import httpx
from pydantic import ValidationError

from app.core.config import Settings
from app.exceptions import DataValidationError, UpstreamServiceError
from app.schemas.upstream import Candle, CandleResponse

logger = logging.getLogger(__name__)


class MarketDataClient:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    async def get_candles(self, symbol: str, lookback: int) -> CandleResponse:
        end = datetime.now(tz=timezone.utc)
        start = end - timedelta(days=max(lookback * 2, 30))
        params = {
            "symbol": symbol,
            "interval": self._settings.market_data_candle_interval,
            "start": start.isoformat(),
            "end": end.isoformat(),
            "limit": str(min(max(lookback, 1), 5000)),
        }
        payload = await self._get_with_retry("/candles", params=params)
        normalized = self._normalize_candle_payload(symbol=symbol, payload=payload)

        if len(normalized.candles) < lookback:
            raise DataValidationError(
                error="insufficient_upstream_data",
                details={
                    "symbol": symbol,
                    "requested_lookback": lookback,
                    "received_candles": len(normalized.candles),
                },
                status_code=422,
            )

        return CandleResponse(
            symbol=normalized.symbol,
            interval=normalized.interval,
            candles=normalized.candles[-lookback:],
        )

    def _normalize_candle_payload(self, symbol: str, payload: Any) -> CandleResponse:
        try:
            if isinstance(payload, dict) and "candles" in payload:
                parsed = CandleResponse.model_validate(payload)
            elif isinstance(payload, list):
                candles = [Candle.model_validate(item) for item in payload]
                parsed = CandleResponse(
                    symbol=symbol,
                    interval=self._settings.market_data_candle_interval,
                    candles=candles,
                )
            else:
                raise DataValidationError(
                    error="unexpected_upstream_payload",
                    details={"payload_type": type(payload).__name__},
                    status_code=422,
                )
            return parsed
        except ValidationError as exc:
            sample_keys: list[str] = []
            if isinstance(payload, dict):
                candles = payload.get("candles")
                if isinstance(candles, list) and candles and isinstance(candles[0], dict):
                    sample_keys = sorted(candles[0].keys())
            elif isinstance(payload, list) and payload and isinstance(payload[0], dict):
                sample_keys = sorted(payload[0].keys())

            raise DataValidationError(
                error="upstream_schema_mismatch",
                details={
                    "message": "Upstream candles did not match expected schema",
                    "sample_candle_keys": sample_keys,
                    "validation_errors": exc.errors()[:5],
                },
                status_code=422,
            ) from exc

    async def _get_with_retry(self, path: str, params: Mapping[str, str]) -> dict | list[dict]:
        attempts = self._settings.market_data_retry_attempts
        timeout = self._settings.market_data_timeout_seconds
        backoff = self._settings.market_data_retry_backoff_seconds
        base_url = str(self._settings.market_data_base_url).rstrip("/")
        url = f"{base_url}{path}"

        last_exc: Exception | None = None
        async with httpx.AsyncClient(timeout=timeout) as client:
            for attempt in range(1, attempts + 1):
                try:
                    response = await client.get(url, params=params)
                    response.raise_for_status()
                    return response.json()
                except (httpx.HTTPError, ValueError) as exc:
                    last_exc = exc
                    logger.warning(
                        "upstream_request_failed",
                        extra={
                            "attempt": attempt,
                            "attempts": attempts,
                            "url": url,
                            "params": dict(params),
                            "error": str(exc),
                        },
                    )
                    if attempt < attempts:
                        await asyncio.sleep(backoff * attempt)

        raise UpstreamServiceError(
            error="upstream_unavailable",
            details={
                "message": f"Failed to fetch upstream data after {attempts} attempts",
                "url": url,
            },
            status_code=502,
        ) from last_exc
