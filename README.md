# ML Engine Platform

A production-focused machine learning platform for market signal prediction, lifecycle governance, and operational monitoring.

## 1) Project Overview

ML Engine Platform provides an end-to-end workflow for feature ingestion, model training/inference, governance, monitoring, and operator control. Phase 5 adds a professional web dashboard, backend hardening, Cloud Run readiness, and deployment-grade documentation.

## 2) Architecture Summary

- **Backend API (FastAPI)**
  - Market data integration
  - Feature engineering
  - Training + inference
  - Model registry + activation
  - Drift/freshness/latency monitoring
  - Audit logging + admin control plane
- **Frontend Dashboard (Next.js App Router)**
  - Overview KPIs
  - Prediction exploration
  - Model management actions
  - Monitoring visualizations
- **Storage**
  - Local artifacts for model files, training history, and prediction audit logs (mount as persistent volume in production)

## 3) Phase Progression (1–5)

- **Phase 1:** Market Data Client + Feature Engineering Pipeline
- **Phase 2:** Training, Inference, Model Registry
- **Phase 3:** Drift Detection, Monitoring, Audit Logging
- **Phase 4:** Async Retraining, Batch Prediction, Control Plane, Docker Hardening
- **Phase 5:** Professional Dashboard UI, Final Backend Hardening, Cloud Run Readiness, Production Documentation

## 4) Feature List

- Public inference APIs (`/predict`, `/predict/batch`)
- Model discovery and activation
- Drift/freshness/latency monitoring endpoints
- Admin retraining controls (API key protected)
- Structured JSON logging + request IDs
- CORS and centralized API error envelopes
- Health and readiness probes (`/health`, `/ready`)
- Production-ready backend and frontend containers
- Professional dashboard with responsive charts/cards

## 5) How to Run Locally

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

Frontend default: `http://localhost:3000`
Backend default: `http://localhost:8000`

## 6) How to Deploy to Cloud Run

> Replace placeholders (`PROJECT_ID`, `REGION`, `REPO`, `SERVICE_NAME`) with your values.

### A. Create Artifact Registry repositories

```bash
gcloud artifacts repositories create ml-engine-backend \
  --repository-format=docker \
  --location=REGION

gcloud artifacts repositories create ml-engine-frontend \
  --repository-format=docker \
  --location=REGION
```

### B. Build and push backend container

```bash
docker build -t REGION-docker.pkg.dev/PROJECT_ID/ml-engine-backend/backend:latest .
docker push REGION-docker.pkg.dev/PROJECT_ID/ml-engine-backend/backend:latest
```

### C. Deploy backend to Cloud Run

```bash
gcloud run deploy ml-engine-backend \
  --image REGION-docker.pkg.dev/PROJECT_ID/ml-engine-backend/backend:latest \
  --platform managed \
  --region REGION \
  --allow-unauthenticated \
  --set-env-vars ENV=production,APP_ENV=cloudrun,CORS_ALLOW_ORIGINS=*
```

### D. Build and push frontend container

```bash
cd frontend
docker build -t REGION-docker.pkg.dev/PROJECT_ID/ml-engine-frontend/frontend:latest .
docker push REGION-docker.pkg.dev/PROJECT_ID/ml-engine-frontend/frontend:latest
```

### E. Deploy frontend to Cloud Run

```bash
gcloud run deploy ml-engine-frontend \
  --image REGION-docker.pkg.dev/PROJECT_ID/ml-engine-frontend/frontend:latest \
  --platform managed \
  --region REGION \
  --allow-unauthenticated \
  --set-env-vars NEXT_PUBLIC_BACKEND_URL=https://<BACKEND_CLOUD_RUN_URL>
```

### F. HTTPS

Cloud Run services are HTTPS-enabled by default on generated URLs. For custom domains, map domain via Cloud Run domain mapping and provision managed certificates.

## 7) Live URL Placeholder

- Backend URL: `https://<backend-service-url>`
- Frontend URL: `https://<frontend-service-url>`

## 8) Screenshots Placeholder

- Dashboard overview: _add screenshot_
- Prediction explorer: _add screenshot_
- Monitoring panel: _add screenshot_

## 9) Tech Stack Summary

- **Backend:** Python, FastAPI, Pydantic, scikit-learn
- **Frontend:** Next.js (App Router), TypeScript, Tailwind CSS, Recharts, Axios
- **Containers:** Docker multi-stage builds, non-root runtime
- **Cloud:** Google Cloud Run + Artifact Registry

## 10) Future Improvements

- Managed DB/warehouse for training and observability history
- Background queue worker for retraining orchestration
- Alerting integrations (PagerDuty/Slack)
- Role-based access control for admin routes
- Canary releases and automated model rollback policies
