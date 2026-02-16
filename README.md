# ML Engine Platform - Phase 1

## Purpose

This service is the **data consumption and feature engineering layer** for a production-style machine learning platform. It retrieves normalized market data from an upstream Market Data Platform over HTTP APIs, validates it, computes deterministic features, and exposes those features via a FastAPI API.

Phase 1 intentionally excludes model training and inference. The goal is to establish a robust foundation for future ML lifecycle components.

## Architecture

The codebase is structured for extension and maintainability:

- `app/api`: API route definitions and dependency wiring.
- `app/clients`: reusable HTTP client integrations (upstream market data).
- `app/core`: configuration and logging.
- `app/features`: feature engineering logic.
- `app/schemas`: strict request/response and upstream validation schemas.
- `app/services`: orchestration layer that coordinates client + feature logic.

This design keeps business logic out of route handlers and allows future components (dataset builders, training, inference APIs) to be added with minimal refactoring.

## Upstream Dependency Model

The service depends on a running upstream Market Data Platform:

- Base URL: `https://YOUR_MARKET_DATA_URL`
- Docs: `https://YOUR_MARKET_DATA_URL/docs`
- OpenAPI: `https://YOUR_MARKET_DATA_URL/openapi.json`

Expected upstream endpoints include:

- `GET /symbols`
- `GET /candles?symbol=&start=&end=`
- `GET /price/latest?symbol=`

Resilience features implemented:

- timeouts
- retry with backoff
- upstream schema validation
- controlled error responses
- structured JSON logging

## Implemented API Endpoints

- `GET /health`
- `GET /api/v1/features?symbol=AAPL&lookback=100`

`/features` response includes:

- symbol
- window used
- upstream latest timestamp
- feature rows (simple return, moving average, rolling volatility)

## Deterministic Feature Set

Feature computations are deterministic for the same ordered candle input:

- simple returns (`pct_change`)
- moving average (rolling mean)
- rolling volatility (rolling std over returns)

## Local Run

1. Create environment file:

```bash
cp .env.example .env
```

2. Update `.env` with your real `MARKET_DATA_BASE_URL`.

3. Install dependencies and run:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

4. Open docs:

- `http://localhost:8000/docs`

## Docker Run

Build image:

```bash
docker build -t ml-feature-platform:phase1 .
```

Run container:

```bash
docker run --rm -p 8000:8000 --env-file .env ml-feature-platform:phase1
```

## Future Phases

This repository is structured to support subsequent additions:

- dataset builders
- training pipelines
- model registry integration
- inference services
- monitoring and dashboards
