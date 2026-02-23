# ML Engine Platform

Production-grade ML control platform for training, inference, model lifecycle governance, and operator observability.

## Project Overview

ML Engine Platform delivers an end-to-end workflow for market-data-based modeling:

- data ingestion + deterministic feature engineering
- supervised training + online inference
- model registry and activation workflows
- drift/freshness/latency monitoring
- audit logging and admin control-plane operations
- operator dashboard for monitoring and interventions

This repository includes both backend and frontend services, each containerized for Google Cloud Run.

---

## Architecture

### Backend (FastAPI)

Core responsibilities:

- Market data client integration
- Feature pipeline and dataset builder
- Model training and prediction serving
- Model registry, version activation, and history
- Monitoring APIs for drift/freshness/latency
- Audit and admin endpoints

### Frontend (Next.js App Router)

Operator dashboard with four primary areas:

- Overview
- Prediction Explorer
- Model Management
- Monitoring

### Persistent Model Storage (Cloud-ready)

`MODEL_REGISTRY_DIR` now supports:

- local filesystem path (e.g., `artifacts/models`) for local dev
- GCS URI (e.g., `gs://ml-engine-platform-models-fintech-labs-123/models`) for durable Cloud Run persistence

> Use GCS in production so versions (`v1`, `v2`, `v3`...) survive scale-to-zero, restarts, and new revisions.

---

## Tech Stack

- **Backend:** Python, FastAPI, Pydantic, NumPy, Pandas
- **ML:** custom linear regressor training pipeline
- **Frontend:** Next.js (App Router), TypeScript, Tailwind CSS, Recharts, Axios
- **Infra:** Docker, Google Cloud Run, Artifact Registry, Google Cloud Storage

---

## API Surface (high-value endpoints)

### Public

- `GET /health`
- `GET /ready`
- `GET /features`
- `GET /predict?symbol=...`
- `POST /predict/batch`
- `GET /models`
- `POST /models/activate/{version}`
- `GET /monitoring/drift`
- `GET /monitoring/history`
- `GET /monitoring/freshness`
- `GET /monitoring/latency`

### Admin (requires `X-API-Key`)

- `POST /admin/train`
- `GET /admin/train/status`
- `POST /admin/activate/{version}`
- `POST /admin/reload`
- `DELETE /admin/audit/clear`

All APIs are also exposed under `/api/v1/*`.

---

## Local Development

### Backend

```bash
cp .env.example .env
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend

```bash
cd frontend
cp .env.example .env.local
npm install
npm run dev
```

- Frontend: `http://localhost:3000`
- Backend: `http://localhost:8000`

---

## Production Deployment (Cloud Run + GCS Persistence)

The commands below assume:

- project: `fintech-labs-123`
- region: `us-central1`
- one artifact registry repo: `ml-engine-repo`
- backend service: `ml-api`
- frontend service: `ml-dashboard`

### 1) One-time setup

```bash
export PROJECT_ID="fintech-labs-123"
export REGION="us-central1"
export REPO_NAME="ml-engine-repo"
export BACKEND_SERVICE="ml-api"
export FRONTEND_SERVICE="ml-dashboard"
export BACKEND_IMAGE="ml-api-image"
export FRONTEND_IMAGE="ml-dashboard-image"

# set your real admin key
export ADMIN_API_KEY="<your-admin-key>"

gcloud auth login
gcloud config set project "$PROJECT_ID"
gcloud config set run/region "$REGION"
gcloud services enable run.googleapis.com artifactregistry.googleapis.com cloudbuild.googleapis.com storage.googleapis.com
gcloud auth configure-docker "${REGION}-docker.pkg.dev" --quiet

gcloud artifacts repositories create "$REPO_NAME" \
  --repository-format=docker \
  --location="$REGION" \
  --description="ML Engine Platform images" || true
```

### 2) Create GCS bucket for durable model registry

```bash
export BUCKET_NAME="ml-engine-platform-models-${PROJECT_ID}"

gcloud storage buckets create "gs://${BUCKET_NAME}" \
  --project="$PROJECT_ID" \
  --location="$REGION" \
  --uniform-bucket-level-access \
  --default-storage-class=STANDARD

cat > lifecycle.json <<'JSON'
{
  "rule": [
    {
      "action": { "type": "Delete" },
      "condition": { "age": 30 }
    }
  ]
}
JSON

gcloud storage buckets update "gs://${BUCKET_NAME}" --lifecycle-file="lifecycle.json"

PROJECT_NUMBER=$(gcloud projects describe "$PROJECT_ID" --format='value(projectNumber)')
RUNTIME_SA="${PROJECT_NUMBER}-compute@developer.gserviceaccount.com"

gcloud storage buckets add-iam-policy-binding "gs://${BUCKET_NAME}" \
  --member="serviceAccount:${RUNTIME_SA}" \
  --role="roles/storage.objectAdmin"
```

### 3) Build + push backend

```bash
BACKEND_TAG=$(date +%Y%m%d-%H%M%S)
docker build --no-cache -t "${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}/${BACKEND_IMAGE}:${BACKEND_TAG}" .
docker push "${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}/${BACKEND_IMAGE}:${BACKEND_TAG}"
```

### 4) Deploy backend (with durable `MODEL_REGISTRY_DIR`)

```bash
gcloud run deploy "$BACKEND_SERVICE" \
  --image "${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}/${BACKEND_IMAGE}:${BACKEND_TAG}" \
  --platform managed \
  --region "$REGION" \
  --allow-unauthenticated \
  --port 8080 \
  --cpu 1 \
  --memory 512Mi \
  --concurrency 80 \
  --min-instances 0 \
  --max-instances 1 \
  --set-env-vars "ENV=production,APP_ENV=cloudrun,ADMIN_API_KEY=${ADMIN_API_KEY},DRIFT_THRESHOLD=0.05,MARKET_DATA_BASE_URL=https://market-data-platform-3qp7bblccq-uc.a.run.app,MODEL_REGISTRY_DIR=gs://${BUCKET_NAME}/models,CORS_ALLOW_ORIGINS=*"

BACKEND_URL=$(gcloud run services describe "$BACKEND_SERVICE" --region "$REGION" --format='value(status.url)')
echo "BACKEND_URL=$BACKEND_URL"
```

### 5) Build + push frontend (with build-time backend URL)

```bash
FRONTEND_TAG=$(date +%Y%m%d-%H%M%S)
docker build --no-cache \
  -f frontend/Dockerfile \
  --build-arg NEXT_PUBLIC_BACKEND_URL="$BACKEND_URL" \
  -t "${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}/${FRONTEND_IMAGE}:${FRONTEND_TAG}" \
  frontend

docker push "${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}/${FRONTEND_IMAGE}:${FRONTEND_TAG}"
```

### 6) Deploy frontend

```bash
gcloud run deploy "$FRONTEND_SERVICE" \
  --image "${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}/${FRONTEND_IMAGE}:${FRONTEND_TAG}" \
  --platform managed \
  --region "$REGION" \
  --allow-unauthenticated \
  --port 8080 \
  --cpu 1 \
  --memory 512Mi \
  --concurrency 80 \
  --min-instances 0 \
  --max-instances 1 \
  --set-env-vars "NEXT_PUBLIC_BACKEND_URL=${BACKEND_URL}"

FRONTEND_URL=$(gcloud run services describe "$FRONTEND_SERVICE" --region "$REGION" --format='value(status.url)')
echo "FRONTEND_URL=$FRONTEND_URL"
```

### 7) Tighten CORS to frontend URL

```bash
gcloud run services update "$BACKEND_SERVICE" \
  --region "$REGION" \
  --update-env-vars "CORS_ALLOW_ORIGINS=${FRONTEND_URL}"
```

---

## Train and Persist `v1`, `v2`, `v3`

```bash
# v1
curl -s -X POST "$BACKEND_URL/admin/train" -H "X-API-Key: $ADMIN_API_KEY" | jq
curl -s "$BACKEND_URL/admin/train/status" -H "X-API-Key: $ADMIN_API_KEY" | jq
curl -s "$BACKEND_URL/models" | jq

# v2
curl -s -X POST "$BACKEND_URL/admin/train" -H "X-API-Key: $ADMIN_API_KEY" | jq
curl -s "$BACKEND_URL/admin/train/status" -H "X-API-Key: $ADMIN_API_KEY" | jq
curl -s "$BACKEND_URL/models" | jq

# v3
curl -s -X POST "$BACKEND_URL/admin/train" -H "X-API-Key: $ADMIN_API_KEY" | jq
curl -s "$BACKEND_URL/admin/train/status" -H "X-API-Key: $ADMIN_API_KEY" | jq
curl -s "$BACKEND_URL/models" | jq
```

### Persistence check across restart/revision

```bash
# force a new backend revision
BACKEND_TAG2=$(date +%Y%m%d-%H%M%S)
docker build --no-cache -t "${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}/${BACKEND_IMAGE}:${BACKEND_TAG2}" .
docker push "${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}/${BACKEND_IMAGE}:${BACKEND_TAG2}"

gcloud run deploy "$BACKEND_SERVICE" \
  --image "${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}/${BACKEND_IMAGE}:${BACKEND_TAG2}" \
  --platform managed \
  --region "$REGION" \
  --allow-unauthenticated \
  --port 8080 \
  --cpu 1 \
  --memory 512Mi \
  --concurrency 80 \
  --min-instances 0 \
  --max-instances 1 \
  --set-env-vars "ENV=production,APP_ENV=cloudrun,ADMIN_API_KEY=${ADMIN_API_KEY},DRIFT_THRESHOLD=0.05,MARKET_DATA_BASE_URL=https://market-data-platform-3qp7bblccq-uc.a.run.app,MODEL_REGISTRY_DIR=gs://${BUCKET_NAME}/models,CORS_ALLOW_ORIGINS=${FRONTEND_URL}"

BACKEND_URL=$(gcloud run services describe "$BACKEND_SERVICE" --region "$REGION" --format='value(status.url)')
curl -s "$BACKEND_URL/models" | jq
```

If persistence is correct, `available_versions` should still include `v1`, `v2`, `v3` and `active_version` should remain populated.

---

## Verification Checklist

```bash
curl -s "$BACKEND_URL/health" | jq
curl -s "$BACKEND_URL/ready" | jq
curl -s "$BACKEND_URL/models" | jq
curl -s "$BACKEND_URL/predict?symbol=AAPL" | jq
curl -I "$FRONTEND_URL"
```

---

## Logging

```bash
gcloud run services logs read "$BACKEND_SERVICE" --region "$REGION" --limit=150
gcloud run services logs read "$FRONTEND_SERVICE" --region "$REGION" --limit=150
```

---

## Notes

- Cloud Run local filesystem is ephemeral. Use `MODEL_REGISTRY_DIR=gs://...` for durable models.
- Frontend must be built with `--build-arg NEXT_PUBLIC_BACKEND_URL=...` to avoid fallback to `http://localhost:8000`.
- Use the canonical service URLs from `gcloud run services describe ... --format='value(status.url)'`.
