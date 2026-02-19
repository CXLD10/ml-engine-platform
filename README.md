# ML Engine Platform

## Project Overview

ML Engine Platform is an internal ML backend that progressed from deterministic feature ingestion (Phase 1), to model training/inference (Phase 2), to lifecycle monitoring and auditability (Phase 3), and now to control-plane-driven production readiness (Phase 4).

## Progression Summary

### Phase 1 — Feature Engine

- Upstream market data ingestion with retries/timeouts.
- Deterministic engineered features via `/features` and `/api/v1/features`.

### Phase 2 — Training & Inference

- Supervised dataset builder.
- Versioned training artifacts in filesystem registry.
- Inference endpoint `/predict`.
- Model discovery APIs (`/models`, `/models/{version}`, `/model/{version}`).

### Phase 3 – Lifecycle & Monitoring

- Activation workflows and model lifecycle metadata.
- Drift detection + freshness + latency monitoring endpoints.
- Structured prediction audit logging with request IDs.

### Phase 4 – Control Plane & Production Hardening

Phase 4 extends the platform into deployable internal-ML infrastructure:

- **Async retraining control plane**: trigger training without blocking serving (`POST /admin/train`) and inspect progress (`GET /admin/train/status`).
- **Admin operations**: model activation (`POST /admin/activate/{version}`), runtime reload (`POST /admin/reload`), and audit reset (`DELETE /admin/audit/clear`).
- **Batch inference**: multi-symbol prediction (`POST /predict/batch`) with graceful per-symbol failure handling.
- **Environment profiles**: `ENV=development|staging|production` adjusts log verbosity defaults for each deployment mode.
- **Security model**: admin routes protected by API key (`X-API-Key`, configured through `ADMIN_API_KEY`).
- **Runtime resilience**: lightweight in-process rate limiting middleware.
- **Cloud readiness**: hardened multi-stage Docker image, non-root runtime, healthcheck, and operational Makefile targets.

## API Endpoints

### Public

- `GET /health`
- `GET /features`
- `GET /predict`
- `POST /predict/batch`
- `GET /predictions/recent`
- `GET /models`
- `GET /models/{version}`
- `GET /model/{version}`
- `POST /models/activate/{version}`
- `GET /monitoring/drift`
- `GET /monitoring/history`
- `GET /monitoring/freshness`
- `GET /monitoring/latency`

### Admin (API key required)

- `POST /admin/train`
- `GET /admin/train/status`
- `POST /admin/activate/{version}`
- `POST /admin/reload`
- `DELETE /admin/audit/clear`

All endpoints are also exposed under `/api/v1/*`.

## Configuration

Copy `.env.example` and adjust values.

Important Phase 4 variables:

- `ENV` — `development`, `staging`, or `production`.
- `ADMIN_API_KEY` — required for `/admin/*` routes.
- `TRAIN_SYMBOLS`, `TRAIN_LOOKBACK`, `TRAIN_TEST_SIZE`, `TRAIN_RANDOM_STATE`, `TRAIN_CV_FOLDS` — default async retraining behavior.
- `RATE_LIMIT_REQUESTS`, `RATE_LIMIT_WINDOW_SECONDS` — request throttling.

## Local Operations

```bash
make run
make train
make test
make docker-build
make docker-run
```

## Docker

```bash
docker build -t ml-engine-platform:phase4 .
docker run --rm -p 8000:8000 --env-file .env -v $(pwd)/artifacts:/app/artifacts ml-engine-platform:phase4
```
