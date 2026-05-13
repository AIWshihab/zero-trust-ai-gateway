# Zero Trust AI Gateway - Complete Project Documentation

## Overview

A FastAPI-based gateway that applies zero-trust controls to AI model access. It supports model onboarding with assessment scans, runtime request evaluation, protection scoring, monitoring, and reporting.

### What It Does

- Authenticated user access with JWT (`user` and `admin` scopes)
- Model registry with risk and sensitivity metadata
- Assessment pipeline to produce base trust score and findings
- Runtime policy checks for prompts, rate signals, and trust signals
- Protection controls that raise posture from base trust to protected trust
- Monitoring and reporting endpoints for operational visibility
- Prompt filtering and output filtering
- Adaptive risk scoring with explainability
- Model evaluation system
- SOC dashboard integration
- AI firewall proxy capabilities

---

## Tech Stack

- **Backend Framework**: FastAPI + Uvicorn
- **Database**: PostgreSQL 16 (via Docker Compose)
- **ORM**: SQLAlchemy (async) + asyncpg
- **Migrations**: Alembic
- **Authentication**: JWT with Python-Jose
- **Password Hashing**: bcrypt/passlib
- **Data Validation**: Pydantic v2
- **Container**: Docker & Docker Compose
- **Frontend**: React/Next.js (separate)

---

## Project Structure

```
zero-trust-ai-gateway/
├── ARCHITECTURE.md                    # Architecture documentation
├── README.md                          # Project readme
├── requirements.txt                   # Root level dependencies
├── docker-compose.yml                 # Docker services orchestration
├── Dockerfile                         # Root Dockerfile
│
├── backend/                           # Backend FastAPI application
│   ├── Dockerfile                     # Backend container config
│   ├── requirements.txt               # Python dependencies
│   ├── alembic.ini                    # Database migration config
│   │
│   ├── alembic/                       # Database migrations
│   │   ├── env.py                     # Migration environment
│   │   ├── script.py.mako             # Migration template
│   │   ├── README                     # Migration guide
│   │   └── versions/                  # Migration files
│   │       ├── 4d2f8e1b9c01_add_dynamic_security_control_plane.py
│   │       ├── 6c8f2a9d1b77_add_attack_sequence_events.py
│   │       ├── 91a0f3d8b2b4_add_adaptive_trust_posture_foundation.py
│   │       ├── b7f4c2a19d03_add_firewall_clients_and_model_risk_history.py
│   │       ├── c1dd4cadc258_add_model_and_request_logs.py
│   │       ├── e3141bc46196_add_model_and_request_logs.py
│   │       ├── ea89563abc2d_create_users_table.py
│   │       └── f31e3f2a7b9d_align_runtime_schema.py
│   │
│   └── app/                           # Application code
│       ├── __init__.py
│       ├── main.py                    # App entrypoint and router wiring
│       │
│       ├── core/                      # Core business logic
│       │   ├── __init__.py
│       │   ├── adaptive_risk_model.py # Adaptive risk scoring
│       │   ├── config.py              # Configuration management
│       │   ├── data_sensitivity.py    # Data sensitivity classification
│       │   ├── database.py            # Database connection setup
│       │   ├── model_trust_engine.py  # Trust score calculation
│       │   ├── monitoring.py          # Monitoring utilities
│       │   ├── output_guard.py        # Output filtering/protection
│       │   ├── policy_engine.py       # Runtime policy evaluation
│       │   ├── protection_engine.py   # Protection controls
│       │   ├── rate_limiter.py        # Rate limiting logic
│       │   ├── security.py            # Security utilities
│       │   └── trust_score.py         # Trust score calculations
│       │
│       ├── models/                    # SQLAlchemy database models
│       │   ├── __init__.py
│       │   ├── attack_sequence_event.py
│       │   ├── firewall.py
│       │   ├── model_posture_event.py
│       │   ├── model_risk_history.py
│       │   ├── model.py               # Main model entity
│       │   ├── request_log.py
│       │   ├── security.py
│       │   ├── user_trust_event.py
│       │   └── user.py                # User/auth entity
│       │
│       ├── routers/                   # API route handlers (endpoints)
│       │   ├── __init__.py
│       │   ├── assessment.py          # Model assessment endpoints
│       │   ├── auth.py                # Authentication endpoints
│       │   ├── detect.py              # Prompt detection endpoints
│       │   ├── evaluation.py          # Model evaluation endpoints
│       │   ├── firewall.py            # Firewall proxy endpoints
│       │   ├── gateway.py             # Main gateway endpoints
│       │   ├── models.py              # Model registry endpoints
│       │   ├── navigation.py          # Navigation/UI endpoints
│       │   ├── protection.py          # Protection control endpoints
│       │   ├── reporting.py           # Reporting/analytics endpoints
│       │   ├── research.py            # Research/testing endpoints
│       │   ├── security.py            # Security endpoints
│       │   ├── testing.py             # Testing utilities endpoints
│       │   └── usage.py               # Usage/inference endpoints
│       │
│       ├── schemas/                   # Pydantic request/response DTOs
│       │   ├── __init__.py
│       │   ├── assessment.py
│       │   ├── auth.py
│       │   ├── common.py
│       │   ├── detect.py
│       │   ├── enums.py               # Enum definitions
│       │   ├── gateway.py
│       │   ├── inference.py
│       │   ├── model.py
│       │   ├── monitoring.py
│       │   ├── protection.py
│       │   ├── reporting.py
│       │   ├── security.py
│       │   └── user.py
│       │
│       ├── services/                  # Business logic and integrations
│       │   ├── __init__.py
│       │   ├── behavioral_tester.py   # Behavioral testing
│       │   ├── chat_errors.py         # Chat/LLM error handling
│       │   └── ...                    # Additional services
│       │
│       ├── testing/                   # Testing utilities
│       │   └── ...
│       │
│       └── ui/                        # UI related code
│
├── frontend/                          # Frontend application
│   ├── Dockerfile                     # Frontend container config
│   └── nginx.conf                     # Nginx configuration
│
├── docs/                              # Documentation
│
└── monitoring/                        # Monitoring configuration
    ├── request_logs.jsonl             # Request logs
    └── dashboards/
        └── metrics.py                 # Dashboard metrics
```

---

## Dependencies

### Backend (Python)

```
annotated-doc==0.0.4
annotated-types==0.7.0
anyio==4.12.1
bcrypt==4.0.1
passlib[bcrypt]==1.7.4
certifi==2026.2.25
cffi==2.0.0
click==8.3.1
cryptography==46.0.5
ecdsa==0.19.1
exceptiongroup==1.3.1
fastapi==0.135.1
h11==0.16.0
httpcore==1.0.9
httptools==0.7.1
httpx==0.28.1
idna==3.11
pyasn1==0.6.3
pycparser==3.0
pydantic==2.12.5
pydantic-settings==2.13.1
pydantic_core==2.41.5
python-dotenv==1.2.2
python-jose[cryptography]==3.5.0
python-multipart==0.0.22
PyYAML==6.0.3
rsa==4.9.1
six==1.17.0
starlette==0.52.1
typing-inspection==0.4.2
typing_extensions==4.15.0
uvicorn==0.42.0
uvloop==0.22.1
watchfiles==1.1.1
websockets==16.0
sqlalchemy[asyncio]>=2.0
aiosqlite
asyncpg
alembic
```

### Infrastructure

- **PostgreSQL 16** - Main database
- **Docker** - Containerization
- **Uvicorn** - ASGI server

---

## Quick Start (Local Development)

### 1) Start PostgreSQL

```bash
docker compose up -d db
```

### 2) Install Python Dependencies

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
```

### 3) Configure Environment

Create/edit `backend/.env`:

```env
DATABASE_URL=postgresql+asyncpg://appuser:apppass@localhost:5432/appdb
SECRET_KEY=change-me-in-production
OPENAI_API_KEY=your_key_here
HF_TOKEN=your_token_here
DEBUG=false
```

### 4) Run Database Migrations

```bash
cd backend
alembic upgrade head
```

### 5) Run API Server

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**API Documentation**: Open `http://localhost:8000/docs`

---

## Quick Start (Docker)

```bash
docker compose up --build
```

**Services:**
- API: `http://localhost:8000`
- Frontend: `http://localhost:3000`
- PostgreSQL: `localhost:5432`

---

## API Overview

**Base URL**: `/api/v1`

### Authentication

- `POST /auth/signup` - Register new user
- `POST /auth/token` - Login and get JWT token
- `GET /auth/me` - Get current user info
- `POST /auth/logout` - Logout

### Models

- `GET /models` - List all models
- `GET /models/{model_id}` - Get specific model
- `POST /models` - Create model (admin)
- `DELETE /models/{model_id}` - Delete model (admin)
- `GET /models/{model_id}/risk` - Get model risk assessment

### Assessment

- `POST /assessment/scan` - Scan and register new model (admin)
- `POST /assessment/{model_id}/scan` - Rescan existing model (admin)

### Detection & Usage

- `POST /detect` - Analyze prompt only (no execution)
- `POST /detect/infer` - Legacy inference path
- `POST /usage/infer` - Safe inference path (recommended)

### Protection

- `POST /protection/{model_id}/enable` - Enable protection (admin)
- `POST /protection/{model_id}/disable` - Disable protection (admin)
- `GET /protection/{model_id}/score` - Get protection score

### Reporting

- `GET /reporting/{model_id}/comparison` - Compare model reports

### Monitoring

- `GET /monitoring/zta/status` - Zero-trust architecture status
- `POST /monitoring/zta/toggle` - Toggle ZTA (admin)
- `GET /monitoring/metrics` - System metrics
- `GET /monitoring/logs` - All logs (admin)
- `GET /monitoring/logs/me` - My logs
- `GET /monitoring/users/{username}/trust` - User trust metrics
- `POST /monitoring/users/{username}/trust/reset` - Reset user trust (admin)
- `GET /monitoring/users/{username}/rate` - User rate limits
- `GET /monitoring/health` - System health

### Firewall

- Various endpoints for firewall/proxy operations (see `firewall.py`)

### Gateway

- Gateway-specific operations (see `gateway.py`)

---

## Model Onboarding Flow

### Recommended Workflow

1. Admin registers/scans a model via `POST /api/v1/assessment/scan`
2. Model receives base trust score and scan summary
3. Runtime inference and reporting only allowed when model is scan-ready
4. Optional protection can be enabled to raise trust posture

### Scan Lifecycle

**States**: `pending` → `in_progress` → `completed`

**Error State**: `failed` is set when scanning errors occur

**Protected State**: `protected` is set after protection is enabled

### Readiness Guard

If a model is not scan-ready, protected routes return `409` with:
- `detail.code = MODEL_NOT_READY`
- Context including `scan_status` and required statuses

---

## Example API Calls (cURL)

### Signup

```bash
curl -X POST "http://localhost:8000/api/v1/auth/signup" \
  -H "Content-Type: application/json" \
  -d '{
    "email":"kira@mail.com",
    "username":"kira",
    "password":"pass1234"
  }'
```

### Login

```bash
curl -X POST "http://localhost:8000/api/v1/auth/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=kira&password=pass1234"
```

### Assessment Scan (Admin)

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

### Safe Inference

```bash
curl -X POST "http://localhost:8000/api/v1/usage/infer" \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "model_id": 1,
    "prompt": "Hello",
    "parameters": {"temperature": 0.2}
  }'
```

---

## Key Components

### Core Business Logic (`backend/app/core/`)

| Component | Purpose |
|-----------|---------|
| `adaptive_risk_model.py` | Calculates and adapts risk scores based on behavior |
| `model_trust_engine.py` | Computes trust scores for models |
| `trust_score.py` | Trust score calculation utilities |
| `policy_engine.py` | Evaluates runtime policies against requests |
| `protection_engine.py` | Manages and applies protection controls |
| `output_guard.py` | Filters and protects model outputs |
| `rate_limiter.py` | Implements rate limiting logic |
| `data_sensitivity.py` | Classifies data sensitivity levels |
| `monitoring.py` | Monitoring and logging utilities |
| `security.py` | Security utilities and helpers |
| `database.py` | Database connection and setup |
| `config.py` | Configuration management |

### Database Models (`backend/app/models/`)

| Model | Purpose |
|-------|---------|
| `user.py` | User accounts with authentication |
| `model.py` | AI model registry |
| `model_risk_history.py` | Historical risk assessments |
| `model_posture_event.py` | Model security posture events |
| `user_trust_event.py` | User trust/risk events |
| `attack_sequence_event.py` | Attack sequence tracking |
| `request_log.py` | Inference request logs |
| `firewall.py` | Firewall rules and policies |

### API Routes (`backend/app/routers/`)

| Router | Purpose |
|--------|---------|
| `auth.py` | User authentication and JWT |
| `models.py` | Model registry operations |
| `assessment.py` | Model scanning and assessment |
| `detect.py` | Prompt analysis and detection |
| `usage.py` | Safe inference operations |
| `protection.py` | Protection control endpoints |
| `reporting.py` | Analytics and reporting |
| `monitoring.py` | System monitoring and health |
| `firewall.py` | Firewall proxy operations |
| `security.py` | Security-related endpoints |
| `evaluation.py` | Model evaluation endpoints |
| `testing.py` | Testing utilities |

### Request/Response Schemas (`backend/app/schemas/`)

Pydantic v2 data validation models for all API request/response payloads.

---

## Database Migrations

Located in `backend/alembic/versions/`, migrations are ordered by timestamp:

1. `ea89563abc2d_create_users_table.py` - Initial user table
2. `c1dd4cadc258_add_model_and_request_logs.py` - Model and request logging
3. `e3141bc46196_add_model_and_request_logs.py` - Additional logging improvements
4. `91a0f3d8b2b4_add_adaptive_trust_posture_foundation.py` - Trust posture foundation
5. `b7f4c2a19d03_add_firewall_clients_and_model_risk_history.py` - Firewall and risk history
6. `6c8f2a9d1b77_add_attack_sequence_events.py` - Attack sequence tracking
7. `4d2f8e1b9c01_add_dynamic_security_control_plane.py` - Dynamic security controls
8. `f31e3f2a7b9d_align_runtime_schema.py` - Runtime schema alignment

**Run migrations with**:
```bash
cd backend
alembic upgrade head      # Apply all migrations
alembic downgrade -1      # Rollback one migration
```

---

## Security Notes

⚠️ **Important:**

- Never commit real API tokens in `.env` or source code
- Rotate any token that was previously exposed
- Keep `SECRET_KEY` strong and private in production
- Use environment variables for all secrets
- JWT tokens are signed with `SECRET_KEY` (change in production)
- Passwords are hashed with bcrypt via passlib
- Database credentials should be managed securely in production

---

## Development Guidelines

### Code Organization Rules

- Preserve API compatibility (breaking changes require version bump)
- Avoid unnecessary refactors unless requested
- Keep changes localized to relevant modules
- Do not rename routes unless explicitly requested

### Important Backend Paths

- Business logic: `backend/app/services`
- API endpoints: `backend/app/routers`
- UI code: `backend/app/ui`
- Core logic: `backend/app/core`

---

## Testing

Test files are located in `backend/tests/`:

- `test_adaptive_risk_model.py` - Risk model tests
- `test_chat_repair.py` - Chat error handling tests
- `test_gateway_interceptor.py` - Gateway interception tests
- `test_policy_engine_research.py` - Policy engine tests
- `test_research_evaluation.py` - Research evaluation tests
- `test_soc_dashboard.py` - SOC dashboard tests
- `test_threat_intelligence.py` - Threat intelligence tests

**Run tests**:
```bash
cd backend
pytest                     # Run all tests
pytest tests/test_*.py     # Run specific test file
pytest -v                  # Verbose output
```

---

## Monitoring & Logs

### Request Logs

Request logs are stored in `monitoring/request_logs.jsonl` in JSONL format (one JSON object per line).

### Dashboard Metrics

Dashboard metrics configuration in `monitoring/dashboards/metrics.py`

### Log Access

- All logs: `GET /monitoring/logs` (admin)
- Current user logs: `GET /monitoring/logs/me`
- User trust logs: `GET /monitoring/users/{username}/trust`

---

## Architecture Principles

1. **Zero Trust**: All requests evaluated against trust policies
2. **Adaptive Risk**: Risk scores adapt based on user behavior and patterns
3. **Protection Controls**: Layered protection that can be enabled/disabled
4. **Monitoring**: Comprehensive request and event logging
5. **Policy Engine**: Centralized policy evaluation
6. **Modular Services**: Business logic separated into focused services

---

## Environment Configuration

### Required Environment Variables

```env
# Database
DATABASE_URL=postgresql+asyncpg://appuser:apppass@localhost:5432/appdb

# Security
SECRET_KEY=your-secret-key-here

# API Keys
OPENAI_API_KEY=your-openai-key
HF_TOKEN=your-huggingface-token

# Logging
DEBUG=false
LOG_LEVEL=INFO
```

### Optional Variables

```env
# Server
HOST=0.0.0.0
PORT=8000

# Database Pool
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=10

# Cache
CACHE_TTL=3600
```

---

## Common Development Tasks

### Add a New API Endpoint

1. Create route handler in appropriate `routers/*.py` file
2. Define request/response schemas in `schemas/`
3. Add business logic in `services/` or `core/`
4. Include router in `app/main.py`
5. Add tests in `tests/`

### Add a Database Model

1. Create model class in `models/`
2. Create migration: `alembic revision --autogenerate -m "description"`
3. Review and adjust migration in `alembic/versions/`
4. Run: `alembic upgrade head`

### Modify Database Schema

```bash
cd backend
# Make changes to models
alembic revision --autogenerate -m "description of changes"
# Review migration file
alembic upgrade head
```

### Run the Application

```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Access Swagger UI

Open `http://localhost:8000/docs` to explore and test API endpoints.

---

## Troubleshooting

### Database Connection Issues

Check `DATABASE_URL` in `.env` and ensure PostgreSQL is running:
```bash
docker compose ps
```

### Migration Errors

View migration history:
```bash
cd backend
alembic history
```

Rollback failed migration:
```bash
alembic downgrade -1
```

### Permission Denied Errors

Ensure user has appropriate role/scope:
- `admin` scope needed for `/assessment/scan`, `/models POST/DELETE`
- `user` scope needed for `/usage/infer`, `/detect`

### API Not Responding

Ensure backend is running and check logs:
```bash
# Check container logs if running in Docker
docker compose logs backend

# Or check terminal output if running locally
```

---

## Performance Optimization

- Database queries use async SQLAlchemy
- Request logging is asynchronous
- Connection pooling configured via asyncpg
- Uvicorn with uvloop for faster event loop

---

## Version History

- **Current Version**: Built with FastAPI 0.135.1, SQLAlchemy 2.0+
- **Python**: 3.9+
- **PostgreSQL**: 16+

---

**Last Updated**: May 7, 2026

For the latest updates and additional documentation, refer to the project repository.
