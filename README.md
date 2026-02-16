# ML Engine Platform

## Project Overview

ML Engine Platform is a production-oriented machine learning backend that starts with deterministic market feature engineering (Phase 1) and extends to dataset construction, model training, registry-backed model lifecycle management, and real-time inference APIs (Phase 2).

The service integrates with an upstream Market Data Platform and keeps API compatibility for existing feature endpoints while adding the model development and serving workflow.

## Progression Summary

### Phase 1 — Feature Engine

Phase 1 implemented a resilient client to consume market data from the Market Data Platform and exposed deterministic engineered features through REST (`/features`, `/api/v1/features`). It established retries, timeout controls, strict schema normalization, and typed error handling.

### Phase 2 — Training & Inference

Phase 2 extends the platform to:

- Build labeled datasets from Phase 1 feature outputs.
- Train and validate versioned ML models using configurable training settings.
- Persist model artifacts, metadata, metrics, and feature schema in a filesystem registry.
- Serve real-time predictions through REST (`/predict`) with model/version discovery APIs (`/models`, `/model/{version}`).
- Keep operational readiness via Dockerization, logging, and unit testing.

## High-Level Architecture (Text Diagram)

1. **Upstream Client Layer (`app/clients`)**
   - `MarketDataClient` calls upstream `/candles` with retries/timeouts.
2. **Feature Layer (`app/features`, `app/services`)**
   - Deterministic feature computation (returns, moving average, rolling volatility).
3. **Dataset Builder (`app/ml/dataset_builder.py`)**
   - Converts feature windows into labeled training datasets (`target_next_return`).
4. **Trainer (`app/ml/trainer.py`)**
   - Splits train/validation, trains model, computes RMSE/R² (+ optional CV), stores artifacts.
5. **Model Registry (`app/ml/registry.py`)**
   - Versioned model storage under `artifacts/models/vN/*` with active version tracking.
6. **Inference Engine (`app/ml/inference.py`)**
   - Loads model from registry, fetches latest features, returns prediction payload.
7. **REST API Layer (`app/api/routes`)**
   - Existing Phase 1 endpoints + Phase 2 endpoints (`/predict`, `/models`, `/model/{version}`).

## API Endpoints

### Phase 1 (Backwards Compatible)

- `GET /health`
- `GET /features?symbol=XYZ&lookback=NN`
- `GET /api/v1/features?symbol=XYZ&lookback=NN`

### Phase 2

- `GET /predict?symbol=XYZ`
- `GET /models`
- `GET /model/{version}`
- Prefixed aliases are also exposed under `/api/v1/*`.

`GET /predict` response example:

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
  "timestamp": "2024-01-01T00:00:00+00:00"
}
```

## Directory Layout

```text
app/
  api/
    dependencies.py
    routes/
      features.py
      health.py
      models.py
      predict.py
  clients/
    market_data.py
  core/
    config.py
    logging.py
  features/
    engineering.py
  ml/
    dataset_builder.py
    trainer.py
    registry.py
    inference.py
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

## Build Dataset + Train Model

1. Configure environment:

```bash
cp .env.example .env
```

2. Install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

3. Train using config:

```bash
python train.py --config configs/train.yaml
```

Training outputs are saved to the model registry (default `artifacts/models`):

- `model.pkl`
- `metadata.json`
- `metrics.json`
- `feature_columns.json`
- `dataset_summary.json`

## Run Inference API

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Open docs:

- `http://localhost:8000/docs`

Call:

```bash
curl "http://localhost:8000/predict?symbol=AAPL"
```

## Configuration

Environment variables are documented in `.env.example`.

Key values:

- `MARKET_DATA_*` for upstream connectivity and resilience
- `MODEL_REGISTRY_DIR` for artifact storage path
- `INFERENCE_LOOKBACK` for default prediction lookback window

Training configuration is externalized in `configs/train.yaml`:

- symbol list
- lookback
- train/validation split
- CV folds
- model hyperparameters

## Docker

```bash
docker build -t ml-engine-platform:phase2 .
docker run --rm -p 8000:8000 --env-file .env -v $(pwd)/artifacts/models:/app/artifacts/models ml-engine-platform:phase2
```

## Reasonable Engineering Decisions

- Implemented a regression target (`target_next_return`) for next-step return prediction.
- Used a lightweight regularized linear regressor baseline for deterministic tabular inference in constrained runtime environments.
- Added confidence as a bounded heuristic (`1 - |prediction|`) for a stable API contract placeholder.
- Kept Phase 1 routes unchanged to preserve client compatibility.
