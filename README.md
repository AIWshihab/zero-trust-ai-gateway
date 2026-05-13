# Zero Trust AI Gateway

Zero Trust AI Gateway is a FastAPI control plane for securing AI model access. It combines model onboarding, prompt and output risk checks, adaptive user trust, device trust scoring, rate-aware policy decisions, firewall-style proxying, SOC monitoring, and a comprehensive browser-based UI.

The backend runs locally with SQLite for quick development or with PostgreSQL through Docker Compose.

---

## What It Does

- Authenticates users with JWT bearer tokens and `user` / `admin` scopes.
- Maintains a model registry with risk, sensitivity, readiness, and protection posture metadata. Global preset models (e.g. Mistral 7B Instruct) are seeded on startup and visible to all users.
- Runs model assessment scans before models are used in protected runtime paths.
- Evaluates prompts and inference requests with policy, rate, user trust, and model-risk signals.
- Tracks device fingerprints, session tokens, and trust scores per device. Emits SOC events on new device logins, risk changes, and revocations.
- Exposes an AI gateway/firewall layer for internal callers and OpenAI-compatible chat completion traffic.
- Tracks logs, trust events, model posture events, SOC alerts, and operational metrics.
- Provides a real system self-test suite (46 tests) that runs live against the running application and reports actual pass/fail results.
- Serves all UI pages server-side as Python string templates with a consistent cybersecurity visual theme.

---

## Tech Stack

- Python 3.11
- FastAPI + Uvicorn
- Pydantic v2
- SQLAlchemy async
- Alembic migrations
- SQLite (`aiosqlite`) for local development
- PostgreSQL 16 (`asyncpg`) via Docker Compose
- pytest + pytest-asyncio for the self-test suite

---

## Project Layout

```text
backend/
  app/
    core/          policy, trust, rate, database, monitoring, config modules
    routers/       API route groups
    schemas/       request and response DTOs
    models/        SQLAlchemy ORM models
    services/      gateway, scanner, registry, firewall, device, and seed services
    testing/       self-test runner (subprocess pytest with JUnit XML capture)
    ui/            server-rendered HTML pages
  alembic/         database migrations
  tests/           test suite (test_gateway_suite.py + test_soc_dashboard.py)
  pytest.ini       asyncio_mode=auto, session-scoped event loop
frontend/          nginx proxy for the backend UI
monitoring/        monitoring assets
docs/              additional project docs
docker-compose.yml local Postgres, backend, and frontend services
```

---

## Quick Start: Local SQLite

```bash
cd backend
python3 -m venv ../.venv
source ../.venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The default database URL is `sqlite+aiosqlite:///./dev.db`. Open:

- Login: `http://localhost:8000/login`
- API docs: `http://localhost:8000/docs`
- Health: `http://localhost:8000/health`

## Quick Start: Docker

```bash
docker compose up --build
```

Starts:

| Service | URL |
|---|---|
| Backend API + UI | `http://localhost:8000` |
| Frontend proxy | `http://localhost:3000` |
| PostgreSQL | `localhost:5432` |

Migrations run automatically before Uvicorn starts.

---

## Environment Variables

Create `backend/.env` for local runs. Docker Compose injects its own values.

```env
DATABASE_URL=sqlite+aiosqlite:///./dev.db
SECRET_KEY=change-me-in-production
DEBUG=false
ZTA_ENABLED=true
MODEL_RISK_ENABLED=true
PROMPT_ANALYSIS_ENABLED=true
RATE_LIMITING_ENABLED=true
USER_TRUST_SCORE_ENABLED=true
CORS_ALLOW_ORIGINS=["http://localhost:3000"]
OPENAI_API_KEY=
HF_TOKEN=
```

For local PostgreSQL instead of SQLite:

```env
DATABASE_URL=postgresql+asyncpg://appuser:apppass@localhost:5432/appdb
```

Then:

```bash
docker compose up -d db
cd backend
alembic upgrade head
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

---

## UI Pages

| Path | Description |
|---|---|
| `/login` | Sign in |
| `/signup` | Create account |
| `/dashboard` | Main dashboard with live system log feed and clickable stat cards |
| `/chat` | AI gateway chat |
| `/my-models` | User's own models |
| `/my-devices` | Device trust — real IP, browser, OS, trust score, sessions, SOC events |
| `/models-manager` | Admin model registry |
| `/control-plane` | Security control plane |
| `/control-center` | Control center |
| `/logs` | Request logs |
| `/research` | Research evaluation |
| `/dashboard/soc` | SOC threat dashboard |
| `/dashboard/firewall` | Firewall admin |
| `/dashboard/models/compare` | Model comparison |
| `/dashboard/security` | Security test suite |
| `/dashboard/demo` | Demo dashboard |
| `/dashboard/evaluation` | Evaluation dashboard |
| `/dashboard/testing` | System self-test (live pytest results) |
| `/account-security` | Account security settings |
| `/gt-mode` | GT mode |

All pages are fully responsive — bottom tab bar on mobile (≤980 px), single column on phones (≤640 px).

---

## API Overview

All versioned routes use the `/api/v1` prefix.

### Authentication

| Method | Path | Notes |
|---|---|---|
| POST | `/auth/signup` | |
| POST | `/auth/token` | Returns JWT |
| GET | `/auth/me` | |
| GET | `/auth/me/profile` | |
| POST | `/auth/logout` | |
| POST | `/auth/change-password` | |

### Model Registry

| Method | Path | Notes |
|---|---|---|
| GET | `/models` | Global + own models |
| GET | `/models/runtime-readiness` | |
| GET | `/models/my` | User-owned models |
| GET | `/models/{id}` | |
| POST | `/models` | Admin |
| DELETE | `/models/{id}` | Admin |
| GET | `/models/{id}/risk` | |
| POST | `/models/user` | Create user-owned model |
| DELETE | `/models/user/{id}` | Delete own model |

### Assessment and Protection

| Method | Path | Notes |
|---|---|---|
| POST | `/assessment/scan` | Admin |
| POST | `/assessment/{id}/scan` | Admin |
| POST | `/protection/{id}/enable` | Admin |
| POST | `/protection/{id}/disable` | Admin |
| GET | `/protection/{id}/score` | |

### Runtime Detection and Inference

| Method | Path |
|---|---|
| POST | `/detect` |
| POST | `/detect/infer` |
| POST | `/usage/infer` |

### Device Trust and Sessions

| Method | Path | Notes |
|---|---|---|
| GET | `/devices/me` | User's devices with current-device flag |
| GET | `/devices/me/sessions` | User's sessions with current-session flag |
| GET | `/devices/me/events` | User's SOC device events |
| GET | `/devices/me/current-info` | Real-time IP, browser, OS for current request |
| POST | `/devices/sessions/{id}/revoke` | Revoke own session |
| GET | `/devices/admin` | Admin: all devices |
| GET | `/devices/admin/events` | Admin: all device events |
| POST | `/devices/{id}/trust` | Admin: set trust status / score |
| POST | `/devices/{id}/revoke` | Admin: revoke device |

Device fingerprints are SHA-256 hashes of `user_id|user-agent|ip_prefix`. Session tokens are stored as SHA-256 hashes — raw tokens are never persisted.

### Gateway and Firewall

| Method | Path | Notes |
|---|---|---|
| POST | `/gateway/intercept` | |
| POST | `/proxy/openai/chat/completions` | |
| GET | `/firewall/clients` | Admin |
| POST | `/firewall/clients` | Admin |
| PATCH | `/firewall/clients/{id}` | Admin |
| POST | `/firewall/proxy` | |

### Security, Reporting, and Research

| Method | Path |
|---|---|
| GET | `/security/control-plane` |
| GET | `/security/controls` |
| POST | `/security/controls` |
| PATCH | `/security/controls/{id}` |
| DELETE | `/security/controls/{id}` |
| GET | `/security/detection-rules` |
| POST | `/security/detection-rules` |
| PATCH | `/security/detection-rules/{id}` |
| DELETE | `/security/detection-rules/{id}` |
| POST | `/security/policy/simulate` |
| POST | `/security/test-suite` |
| POST | `/security/models/compare` |
| GET | `/reporting/research-metrics` |
| GET | `/research/evaluation-report` |
| GET | `/research/evaluation-dataset` |
| GET | `/research/policy-replay` |
| GET | `/research/control-effectiveness` |
| GET | `/research/counterfactual-analysis` |
| GET | `/research/risk-drift` |

### Monitoring

| Method | Path | Notes |
|---|---|---|
| GET | `/monitoring/zta/status` | |
| POST | `/monitoring/zta/toggle` | Admin |
| GET | `/monitoring/metrics` | |
| GET | `/monitoring/logs` | Admin |
| GET | `/monitoring/logs/me` | |
| GET | `/monitoring/research/summary` | |
| GET | `/monitoring/users/{username}/trust` | |
| GET | `/monitoring/users/trust/all` | |
| POST | `/monitoring/users/{username}/trust/reset` | Admin |
| GET | `/monitoring/users/{username}/trust/events` | |
| GET | `/monitoring/models/{id}/posture/events` | |
| GET | `/monitoring/users/{username}/rate` | |
| GET | `/monitoring/users/rate/all` | |
| GET | `/monitoring/health` | |
| GET | `/monitoring/soc/attack-timeline` | Admin |
| GET | `/monitoring/soc/user-anomalies` | Admin |
| GET | `/monitoring/soc/threat-heatmap` | Admin |
| GET | `/monitoring/soc/alerts` | Admin |

### System and Testing

| Method | Path | Notes |
|---|---|---|
| GET | `/system/state` | |
| GET | `/navigation/options` | |
| GET | `/evaluation/scenarios` | |
| GET | `/evaluation/compare/{id}` | |
| GET | `/evaluation/report` | |
| GET | `/testing/run-soc-tests` | Runs live pytest suite, returns real results |

---

## Self-Test Suite

The self-test page at `/dashboard/testing` runs a live pytest suite (46 tests) as a subprocess and displays real results — no mocked data.

**Test coverage:**

| Area | Tests |
|---|---|
| Health & system state | 3 |
| Authentication (auth rejection, 401/422 paths) | 4 |
| Model registry (list, schema, runtime readiness, visibility) | 5 |
| Security controls and detection rules | 4 |
| Monitoring metrics and admin logs | 4 |
| SOC endpoints (attack timeline, heatmap, anomalies, alerts) | 5 |
| Devices and sessions | 5 |
| Firewall clients | 2 |
| ZTA status and policy simulation | 2 |
| Trust profiles and reporting | 4 |
| Original SOC dashboard tests | 7 |

Tests run with `asyncio_mode=auto` and a session-scoped event loop (so asyncpg connection pools are reused across tests). Results include actual pytest node IDs, per-test durations in milliseconds, and full failure messages.

To run directly:

```bash
cd backend
pytest tests
```

---

## Device Trust System

Every login creates or updates a device record keyed by a fingerprint derived from `user_id`, `User-Agent`, and the first three octets of the client IP. The trust score starts at 60 and adjusts based on:

- Login count (up to +20 over repeated logins)
- Failed attempts (−10 per failure)
- Status cap: new devices are capped at 65 until they reach 3 successful logins

Trust levels: `low` (≥80) / `medium` (≥55) / `high` (≥30) / `critical` (<30).

SOC events are emitted on new device login, known device login, high-risk login, device revocation, session revocation, and admin trust changes. The My Devices page shows real-time device info (IP, browser, OS) detected from the current request — no fake or simulated data.

---

## Model Onboarding Flow

1. Admin scans or registers a model via `POST /api/v1/assessment/scan`.
2. The scanner records metadata, findings, base trust score, and scan status.
3. Runtime endpoints check model readiness before inference.
4. Optional protection can be enabled via `POST /api/v1/protection/{id}/enable`.
5. Monitoring exposes request logs, trust changes, posture events, and SOC summaries.

Scan status: `pending → in_progress → completed`. `failed` on error, `protected` after protection is enabled.

Unready models return `409` with a structured `MODEL_NOT_READY` detail.

---

## Example cURL

### Create a User

```bash
curl -X POST "http://localhost:8000/api/v1/auth/signup" \
  -H "Content-Type: application/json" \
  -d '{"email":"kira@example.com","username":"kira","password":"pass1234"}'
```

### Log In

```bash
curl -X POST "http://localhost:8000/api/v1/auth/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=kira&password=pass1234"
```

### Run Safe Inference

```bash
curl -X POST "http://localhost:8000/api/v1/usage/infer" \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"model_id":1,"prompt":"Summarize this request","parameters":{"temperature":0.2}}'
```

### Use the Gateway Interceptor

```bash
curl -X POST "http://localhost:8000/api/v1/gateway/intercept" \
  -H "x-gateway-api-key: key1" \
  -H "Content-Type: application/json" \
  -d '{
    "model_id": "1",
    "prompt": "Explain the zero trust decision.",
    "client_id": "demo-client",
    "external_user_id": "user-123",
    "policy_context": {},
    "parameters": {}
  }'
```

### Get Current Device Info

```bash
curl "http://localhost:8000/api/v1/devices/me/current-info" \
  -H "Authorization: Bearer <TOKEN>"
```

---

## Development Notes

- Use Alembic migrations for all schema changes. `AUTO_INIT_SCHEMA=false` is the normal setting for development and production.
- The Docker backend image must be rebuilt (`docker compose build backend`) to pick up any file changes — the source is not volume-mounted.
- Use `/docs` during development to inspect exact request and response schemas.
- Admin-only endpoints require a token whose scopes include `admin`.
- Never log passwords, raw JWT tokens, provider API keys, or database credentials.

---

## Security Notes

- Do not commit real API keys, JWT secrets, database credentials, or Hugging Face/OpenAI tokens.
- Replace `SECRET_KEY` before production use.
- Rotate any secret that has been exposed in logs, commits, screenshots, or shared environments.
- Review gateway API key and firewall client management before exposing proxy endpoints outside a trusted network.
- Session tokens are stored as truncated SHA-256 hashes. Raw tokens are never persisted.
