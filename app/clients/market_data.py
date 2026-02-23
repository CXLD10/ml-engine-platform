from __future__ import annotations

import asyncio
import logging
from collections.abc import Mapping
from datetime import datetime, timedelta, timezone
from typing import Any

import httpx
from pydantic import ValidationError

from app.core.config import Settings
from app.exceptions import DataValidationError, UpstreamServiceError
from app.schemas.p1 import (
    CandleResponse,
    CompanyResponse,
    FundamentalsResponse,
    MarketStatusResponse,
    P1ErrorResponse,
    QuoteResponse,
)

logger = logging.getLogger(__name__)

ERROR_CODE_MAP = {
    "EXCHANGE_UNAVAILABLE": 503,
    "RATE_LIMITED": 429,
    "INVALID_INPUT": 422,
    "SCHEMA_MISMATCH": 502,
    "STALE_DATA": 502,
    "PARTIAL_DATA": 502,
}
RETRYABLE_CODES = {"EXCHANGE_UNAVAILABLE", "RATE_LIMITED", "STALE_DATA", "PARTIAL_DATA"}


class MarketDataClient:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    async def get_quote(self, symbol: str, exchange: str) -> QuoteResponse:
        payload = await self._get_with_retry("/quote", {"symbol": symbol, "exchange": exchange})
        payload = self._normalize_endpoint_payload("/quote", payload)
        return self._validate_payload(QuoteResponse, payload)

    async def get_intraday(self, symbol: str, exchange: str, interval: str = "1m", limit: int = 300) -> CandleResponse:
        payload = await self._get_with_retry(
            "/intraday", {"symbol": symbol, "exchange": exchange, "interval": interval, "limit": str(limit)}
        )
        payload = self._normalize_endpoint_payload("/intraday", payload)
        return self._validate_payload(CandleResponse, payload)

    async def get_historical(self, symbol: str, exchange: str, start: datetime, end: datetime, interval: str = "1d") -> CandleResponse:
        payload = await self._get_with_retry(
            "/historical",
            {
                "symbol": symbol,
                "exchange": exchange,
                "interval": interval,
                "start": start.astimezone(timezone.utc).isoformat(),
                "end": end.astimezone(timezone.utc).isoformat(),
            },
        )
        payload = self._normalize_endpoint_payload("/historical", payload)
        return self._validate_payload(CandleResponse, payload)

    async def get_fundamentals(self, symbol: str, exchange: str) -> FundamentalsResponse:
        payload = await self._get_with_retry("/fundamentals", {"symbol": symbol, "exchange": exchange})
        payload = self._normalize_endpoint_payload("/fundamentals", payload)
        return self._validate_payload(FundamentalsResponse, payload)

    async def get_company(self, symbol: str, exchange: str) -> CompanyResponse:
        payload = await self._get_with_retry("/company", {"symbol": symbol, "exchange": exchange})
        payload = self._normalize_endpoint_payload("/company", payload)
        return self._validate_payload(CompanyResponse, payload)

    async def get_market_status(self, exchange: str) -> MarketStatusResponse:
        payload = await self._get_with_retry("/market-status", {"exchange": exchange})
        payload = self._normalize_endpoint_payload("/market-status", payload)
        return self._validate_payload(MarketStatusResponse, payload)

    async def get_candles(self, symbol: str, lookback: int, exchange: str = "NASDAQ") -> CandleResponse:
        end = datetime.now(tz=timezone.utc)
        start = end - timedelta(days=max(lookback * 3, 30))
        response = await self.get_historical(symbol=symbol, exchange=exchange, start=start, end=end, interval="1d")
        if len(response.candles) < lookback:
            raise DataValidationError(
                error="insufficient_upstream_data",
                details={"symbol": symbol, "requested_lookback": lookback, "received_candles": len(response.candles)},
                status_code=422,
            )
        response.candles = response.candles[-lookback:]
        return response


    def _normalize_endpoint_payload(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(payload, dict):
            return payload

        normalized = dict(payload)
        if path == "/quote" and isinstance(payload.get("quote"), dict):
            normalized.update(payload["quote"])
        if path in {"/intraday", "/historical"} and isinstance(payload.get("data"), dict):
            normalized.update(payload["data"])
        if path == "/fundamentals" and all(key in payload for key in ["market_cap", "pe_ratio"]):
            fundamentals_fields = {
                key: payload.get(key)
                for key in [
                    "market_cap", "pe_ratio", "forward_pe", "eps", "revenue", "revenue_growth", "ebitda",
                    "net_income", "debt_to_equity", "roe", "sector", "industry", "country", "currency",
                ]
            }
            normalized["fundamentals"] = fundamentals_fields
        if path == "/company" and isinstance(payload.get("company"), dict):
            normalized.update(payload["company"])
        if path == "/market-status" and isinstance(payload.get("market_status"), dict):
            market = payload["market_status"]
            normalized.update(
                {
                    "is_open": market.get("is_open", market.get("market_open")),
                    "session": market.get("session", "unknown"),
                    "timezone": market.get("timezone", "UTC"),
                    "server_time_utc": market.get("server_time_utc", market.get("timestamp")),
                    "local_exchange_time": market.get("local_exchange_time", market.get("timestamp")),
                }
            )
        return normalized

    def _validate_payload(self, model_cls, payload: dict[str, Any]) -> Any:
        try:
            return model_cls.model_validate(payload)
        except ValidationError as exc:
            raise DataValidationError(
                error="upstream_schema_mismatch",
                details={"message": "Payload does not match schema_version 1.1 contract", "validation_errors": str(exc)},
                status_code=422,
            ) from exc

    async def _get_with_retry(self, path: str, params: Mapping[str, str]) -> dict[str, Any]:
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
                    payload = response.json()
                    if response.status_code >= 400:
                        self._raise_upstream_error(payload)
                    return payload
                except UpstreamServiceError as exc:
                    last_exc = exc
                    retryable = exc.error in RETRYABLE_CODES
                    if attempt < attempts and retryable:
                        await asyncio.sleep(backoff * attempt)
                        continue
                    raise
                except (httpx.HTTPError, ValueError) as exc:
                    last_exc = exc
                    logger.warning("upstream_request_failed", extra={"attempt": attempt, "url": url, "params": dict(params), "error": str(exc)})
                    if attempt < attempts:
                        await asyncio.sleep(backoff * attempt)

        raise UpstreamServiceError(
            error="EXCHANGE_UNAVAILABLE",
            details={"message": f"Failed upstream call after {attempts} attempts", "url": url},
            status_code=503,
        ) from last_exc

    def _raise_upstream_error(self, payload: Any) -> None:
        if isinstance(payload, dict):
            try:
                parsed = P1ErrorResponse.model_validate(payload)
                code = ERROR_CODE_MAP.get(parsed.error_code, 502)
                raise UpstreamServiceError(error=parsed.error_code, details=parsed.message, status_code=code)
            except ValidationError:
                pass
        raise UpstreamServiceError(error="SCHEMA_MISMATCH", details="Malformed upstream error payload", status_code=502)
