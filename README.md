# ML Engine Platform

## Project Overview

ML Engine Platform is a production-oriented machine learning backend that starts with deterministic market feature engineering (Phase 1), expands into model development and serving (Phase 2), and now adds production hardening controls (Phase 3) for lifecycle governance and runtime observability.

## Progression Summary

### Phase 1 — Feature Engine

Phase 1 implemented a resilient client to consume market data from the Market Data Platform and exposed deterministic engineered features through REST (`/features`, `/api/v1/features`).

### Phase 2 — Training & Inference

Phase 2 added:

- Dataset builder for supervised labels.
- Model training and validation.
- Versioned artifacts in a filesystem model registry.
- Real-time inference (`/predict`).
- Model discovery endpoints (`/models`, `/model/{version}`).

### Phase 3 – Lifecycle & Monitoring

Phase 3 turns the service into a small internal ML platform with production controls:

- **Model lifecycle controls**: multiple versions, active model designation, promotion/activation (`POST /models/activate/{version}`), and rollback by re-activating a prior version.
- **Structured registry metadata**: `registry.json` now tracks created-at timestamps, training/validation metrics, dataset window, and active version.
- **Prediction audit trail**: each inference has a unique `request_id` and is persisted as structured JSON with version, features, output, timestamp, and latency.
- **Drift detection**: rolling feature statistics are compared against training baselines with configurable thresholding (`DRIFT_THRESHOLD`).
- **Observability endpoints**: drift, performance history, freshness, and latency monitoring APIs.
- **Production hardening**: monitoring logic is modularized outside API routes and configurable through environment variables.

## High-Level Architecture (Text Diagram)

1. **Upstream Client Layer (`app/clients`)**
   - `MarketDataClient` calls upstream `/candles` with retries/timeouts.
2. **Feature Layer (`app/features`, `app/services`)**
   - Deterministic feature computation.
3. **Dataset Builder (`app/ml/dataset_builder.py`)**
   - Converts feature windows into labeled datasets.
4. **Trainer (`app/ml/trainer.py`)**
   - Trains versioned models and stores validation + baseline feature stats.
5. **Lifecycle Registry (`app/registry/lifecycle.py`)**
   - Persists artifacts and structured registry metadata (`registry.json`, `training_history.json`).
6. **Inference Engine (`app/ml/inference.py`)**
   - Runs prediction and emits audit + monitoring signals.
7. **Audit Logging (`app/logging/audit.py`)**
   - Structured JSON prediction log with retrieval support.
8. **Monitoring Modules (`app/monitoring`)**
   - `drift.py`: feature drift checks.
   - `freshness.py`: upstream/training/inference freshness tracking.
   - `metrics.py`: rolling latency tracking.
9. **REST API Layer (`app/api/routes`)**
   - Phase 1 + 2 endpoints remain compatible, with added Phase 3 monitoring/lifecycle APIs.

## API Endpoints

### Phase 1 (Backwards Compatible)

- `GET /health`
- `GET /features?symbol=XYZ&lookback=NN`
- `GET /api/v1/features?symbol=XYZ&lookback=NN`

### Phase 2 + 3

- `GET /predict?symbol=XYZ`
- `GET /predictions/recent?limit=N`
- `GET /models`
- `GET /models/{version}`
- `GET /model/{version}` (legacy compatibility)
- `POST /models/activate/{version}`
- `GET /monitoring/drift`
- `GET /monitoring/history`
- `GET /monitoring/freshness`
- `GET /monitoring/latency`

All APIs are also exposed under `/api/v1/*`.

## Directory Layout

```text
app/
  api/
    dependencies.py
    routes/
      features.py
      health.py
      models.py
      monitoring.py
      predict.py
  clients/
    market_data.py
  core/
    config.py
    logging.py
  features/
    engineering.py
  logging/
    audit.py
  ml/
    dataset_builder.py
    trainer.py
    registry.py
    inference.py
  monitoring/
    drift.py
    freshness.py
    metrics.py
  registry/
    lifecycle.py
  schemas/
    error.py
    features.py
    ml.py
    upstream.py
  services/
    feature_service.py
configs/
  train.yaml
artifacts/
  models/
tests/
train.py
```

## Configuration

Environment variables are documented in `.env.example`.

Key Phase 3 values:

- `DRIFT_THRESHOLD` — threshold for drift deviation checks.
- `AUDIT_LOG_LIMIT` — max entries returned by `/predictions/recent`.
- `AUDIT_LOG_FILE` — structured JSON lines audit log destination.

## Docker

Docker workflow remains unchanged and compatible:

```bash
docker build -t ml-engine-platform:phase3 .
docker run --rm -p 8000:8000 --env-file .env -v $(pwd)/artifacts:/app/artifacts ml-engine-platform:phase3
```

## Example Prediction Response (Phase 3)

```json
{
  "symbol": "XYZ",
  "prediction": 0.73,
  "confidence": 0.82,
  "model_version": "v1",
  "features": {
    "close": 102.0,
    "simple_return": 0.01,
    "moving_average": 101.5,
    "rolling_volatility": 0.02
  },
  "timestamp": "2024-01-01T00:00:00+00:00",
  "request_id": "5a801341-6492-4cf5-a4d9-030052454008",
  "latency_ms": 7.12
}
```
