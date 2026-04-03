# Zero Trust AI Gateway

A FastAPI-based gateway that applies zero-trust controls to AI model access.

It supports model onboarding with assessment scans, runtime request evaluation, protection scoring, monitoring, and reporting.

## What It Does

- Authenticated user access with JWT (`user` and `admin` scopes).
- Model registry with risk and sensitivity metadata.
- Assessment pipeline to produce base trust score and findings.
- Runtime policy checks for prompts, rate signals, and trust signals.
- Protection controls that raise posture from base trust to protected trust.
- Monitoring and reporting endpoints for operational visibility.

## Tech Stack

- FastAPI + Uvicorn
- SQLAlchemy (async) + asyncpg
- Alembic migrations
- PostgreSQL 16 (via Docker Compose)

## Project Layout

- `backend/app/main.py` app entrypoint and router wiring
- `backend/app/routers` API route modules
- `backend/app/schemas` request/response DTOs (separate files)
- `backend/app/models` SQLAlchemy models
- `backend/app/services` business logic and integrations
- `backend/alembic` migrations
- `docker-compose.yml` local Postgres + backend service

## Quick Start (Local)

### 1) Start Postgres

```bash
docker compose up -d db
```

### 2) Install Python deps

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
```

### 3) Configure environment

Edit `backend/.env` and set at least:

```env
DATABASE_URL=postgresql+asyncpg://appuser:apppass@localhost:5432/appdb
SECRET_KEY=change-me-in-production
OPENAI_API_KEY=
HF_TOKEN=
DEBUG=false
```

### 4) Run migrations

```bash
cd backend
alembic upgrade head
```

### 5) Run API

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Open docs at `http://localhost:8000/docs`.

## Quick Start (Docker)

```bash
docker compose up --build
```

This runs:

- API: `http://localhost:8000`
- Postgres: `localhost:5432`

## API Overview

Base prefix: `/api/v1`

- Auth
- `POST /auth/signup`
- `POST /auth/token`
- `GET /auth/me`
- `POST /auth/logout`

- Models
- `GET /models`
- `GET /models/{model_id}`
- `POST /models` (admin)
- `DELETE /models/{model_id}` (admin)
- `GET /models/{model_id}/risk`

- Assessment
- `POST /assessment/scan` (admin, scan + upsert)
- `POST /assessment/{model_id}/scan` (admin, rescan existing model)

- Detection and Usage
- `POST /detect` (prompt analysis only)
- `POST /detect/infer` (legacy inference path)
- `POST /usage/infer` (safe inference path)

- Protection
- `POST /protection/{model_id}/enable` (admin)
- `POST /protection/{model_id}/disable` (admin)
- `GET /protection/{model_id}/score`

- Reporting
- `GET /reporting/{model_id}/comparison`

- Monitoring
- `GET /monitoring/zta/status`
- `POST /monitoring/zta/toggle` (admin)
- `GET /monitoring/metrics`
- `GET /monitoring/logs` (admin)
- `GET /monitoring/logs/me`
- `GET /monitoring/users/{username}/trust`
- `POST /monitoring/users/{username}/trust/reset` (admin)
- `GET /monitoring/users/{username}/rate`
- `GET /monitoring/health`

## Model Onboarding Flow

### Recommended flow

1. Admin registers/scans a model via `POST /api/v1/assessment/scan`.
2. Model gets base trust score and scan summary.
3. Runtime inference and reporting are allowed only when model is scan-ready.
4. Optional protection can be enabled to raise trust posture.

### Scan lifecycle

`pending -> in_progress -> completed`

`failed` is set when scanning errors.

`protected` is set after protection is enabled.

### Readiness guard

If a model is not scan-ready, protected routes return `409` with:

- `detail.code = MODEL_NOT_READY`
- context including `scan_status` and required statuses

## Example cURL

### Signup

```bash
curl -X POST "http://localhost:8000/api/v1/auth/signup" \
  -H "Content-Type: application/json" \
  -d '{"email":"kira@mail.com","username":"kira","password":"pass1234"}'
```

### Login (token)

```bash
curl -X POST "http://localhost:8000/api/v1/auth/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=kira&password=pass1234"
```

### Assessment scan (admin token)

```bash
curl -X POST "http://localhost:8000/api/v1/assessment/scan" \
  -H "Authorization: Bearer <ADMIN_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My Model",
    "model_type": "custom_api",
    "provider_name": "internal",
    "endpoint": "http://localhost:9000/infer"
  }'
```

### Safe inference

```bash
curl -X POST "http://localhost:8000/api/v1/usage/infer" \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"model_id":1,"prompt":"Hello","parameters":{"temperature":0.2}}'
```

## Security Notes

- Never commit real API tokens in `.env` or source code.
- Rotate any token that was previously exposed.
- Keep `SECRET_KEY` strong and private in production.
