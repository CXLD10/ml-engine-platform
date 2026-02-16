import asyncio
import logging
from collections.abc import Mapping
from datetime import datetime, timedelta, timezone

import httpx
from pydantic import ValidationError

from app.core.config import Settings
from app.exceptions import DataValidationError, UpstreamServiceError
from app.schemas.upstream import CandleResponse

logger = logging.getLogger(__name__)


class MarketDataClient:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    async def get_candles(self, symbol: str, lookback: int) -> CandleResponse:
        end = datetime.now(tz=timezone.utc)
        start = end - timedelta(days=max(lookback * 2, 30))
        params = {
            "symbol": symbol,
            "start": start.isoformat(),
            "end": end.isoformat(),
        }
        payload = await self._get_with_retry("/candles", params=params)

        try:
            parsed = CandleResponse.model_validate(payload)
        except ValidationError as exc:
            raise DataValidationError("Upstream candle response schema mismatch") from exc

        if len(parsed.candles) < lookback:
            raise DataValidationError(
                f"Insufficient candle data from upstream for symbol={symbol}; "
                f"requested lookback={lookback}, got={len(parsed.candles)}"
            )

        return CandleResponse(symbol=parsed.symbol, candles=parsed.candles[-lookback:])

    async def _get_with_retry(self, path: str, params: Mapping[str, str]) -> dict:
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
                    data = response.json()
                    if not isinstance(data, dict):
                        raise UpstreamServiceError("Unexpected upstream response type")
                    return data
                except (httpx.HTTPError, ValueError, UpstreamServiceError) as exc:
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
            f"Failed to fetch upstream data after {attempts} attempts"
        ) from last_exc
