# ML Engine Platform - Phase 1

## Purpose

This service is the **data consumption and feature engineering layer** for a production-style machine learning platform. It consumes normalized market data from the Market Data Platform over HTTP APIs, validates upstream contracts, computes deterministic features, and exposes those features via REST.

Phase 1 intentionally excludes training, inference, registry, and dashboards.

## Upstream Dependency

This service integrates with the Market Data Platform (read-only HTTP):

- Base URL: `https://market-data-platform-3qp7bblccq-uc.a.run.app`
- Swagger: `https://market-data-platform-3qp7bblccq-uc.a.run.app/docs`
- Redoc: `https://market-data-platform-3qp7bblccq-uc.a.run.app/redoc`
- Health: `https://market-data-platform-3qp7bblccq-uc.a.run.app/health`

Expected upstream capabilities include:

- `GET /symbols`
- `GET /price/latest?symbol=...`
- `GET /trades?symbol=...&start=...&end=...&limit=...`
- `GET /candles?symbol=...&interval=1m&start=...&end=...`
- typed error payloads (`error`, `details`, `status`)

## Architecture

- `app/api`: route handlers + DI wiring only
- `app/clients`: upstream HTTP clients
- `app/services`: orchestration/business workflows
- `app/features`: deterministic feature engineering
- `app/schemas`: Pydantic data contracts
- `app/core`: config and structured logging

Business logic is intentionally outside route handlers for future extensibility.

## Implemented API

- `GET /health`
- `GET /features?symbol=AAPL&lookback=100`
- `GET /api/v1/features?symbol=AAPL&lookback=100` (aliased with prefix)

`/features` response includes:

- `symbol`
- `window_used`
- `upstream_latest_timestamp`
- `features[]` rows with:
  - `simple_return`
  - `moving_average`
  - `rolling_volatility`

Error responses are typed:

```json
{
  "error": "invalid_lookback",
  "details": {"max_lookback": 1000, "provided": 5000},
  "status": 422
}
```

## Resilience + Observability

- timeout and retry/backoff around upstream calls
- upstream schema normalization and validation (supports canonical OHLCV and aliased OHLC fields)
- controlled service errors for upstream failures and invalid data
- JSON structured logs to stdout/stderr

## Local Run

```bash
cp .env.example .env
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Then open:

- `http://localhost:8000/docs`

## Docker

```bash
docker build -t ml-feature-platform:phase1 .
docker run --rm -p 8000:8000 --env-file .env ml-feature-platform:phase1
```

## Future Extension

The structure is designed for adding dataset builders, training pipelines, model lifecycle APIs, inference, and monitoring in future phases without major refactors.
