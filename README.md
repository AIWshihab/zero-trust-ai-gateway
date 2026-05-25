# Zero Trust AI Gateway

Zero Trust AI Gateway is a FastAPI control plane and dashboard for secure AI model access. It combines Gateway Chat, model registry management, prompt and output risk checks, device trust, session tracking, real SOC/security monitoring, firewall-style proxy routes, and a Chrome Manifest V3 browser extension flow.

The project is built to run locally with SQLite for fast development, or with PostgreSQL through Docker Compose or a production deployment.

## Core Features

- **Gateway Chat**: ChatGPT-style secure chat UI backed by persisted chat sessions and messages.
- **Policy-first inference**: Prompts are screened before model execution, with `ALLOW`, `CHALLENGE`, and `BLOCK` decisions.
- **Full-message routing**: Chat and extension requests can pass structured message history to model routes.
- **Model registry**: Admin-managed and user-owned models with readiness, risk, provider, and visibility metadata.
- **Security Monitor / SOC**: Real request logs, device events, alert summaries, model posture, trust changes, and extension activity.
- **Device trust**: Device fingerprints, sessions, revocation, trust scores, browser/OS context, and audit events.
- **Gateway/API firewall**: Gateway key validation, OpenAI-compatible proxy routes, and firewall client management.
- **Browser extension support**: Smart install/connect wizard, one-time pairing tokens, setup-session polling, developer ZIP download, and future Chrome Web Store support.
- **Admin/user access separation**: Normal users can chat, manage their devices, and use allowed models; dangerous controls remain admin-only.

## One-Page Beginner Guide

This section is for people with no technical background who just want to use the gateway.

### What This App Is

Zero Trust AI Gateway is a secure AI dashboard. Instead of sending prompts directly to a model, users send prompts through the gateway first. The gateway checks risk, applies policy, logs security events, and then decides whether the request should be allowed, challenged, or blocked.

### What You Can Do

1. **Chat safely**: Open **Secure Chat** and ask questions through the gateway.
2. **Watch security activity**: Open **Security Monitor** to see real requests, blocks, alerts, devices, and extension events.
3. **Manage models**: Open **Models** to see which AI models are available.
4. **Connect your browser**: Click **Add Browser Extension** to connect Chrome to the gateway.
5. **Review your account**: Open **Account** to manage password, sessions, and device security.

### First-Time Local Setup

If someone gives you this project folder and says “run it locally,” do this:

```bash
cd backend
python3 -m venv ../.venv
source ../.venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Then open:

```text
http://localhost:8000/dashboard
```

If you do not have an account, open:

```text
http://localhost:8000/signup
```

### How To Use Secure Chat

1. Go to `http://localhost:8000/dashboard/chat`.
2. Choose a model from the model picker.
3. Type your message.
4. The gateway checks the request.
5. If safe, the model responds.
6. If risky, the gateway may challenge or block it.

The gateway should never show fake security data. If a model provider cannot answer, it should say the provider could not complete inference.

### How To Use The Browser Extension

Click **Add Browser Extension** in the dashboard.

The page will guide you through:

1. **Step 1: Install**
2. **Step 2: Connect**
3. **Step 3: Test**

For local development:

1. Click **Download Developer Extension**.
2. Open Chrome.
3. Go to `chrome://extensions`.
4. Turn on **Developer Mode**.
5. Click **Load unpacked**.
6. Select the `browser-extension` folder.
7. Go back to the gateway setup page.
8. Copy the connect URL.
9. Open the extension popup.
10. Paste the connect URL.
11. Click **Connect**.

For production:

1. Click **Add to Chrome**.
2. Chrome opens the Chrome Web Store.
3. Click **Add to Chrome** in Chrome.
4. Return to the gateway setup page.
5. Open the extension popup.
6. Paste the connect URL if it is not already filled.
7. Click **Connect**.

Important: the dashboard cannot secretly install a Chrome extension. Chrome requires the user to approve installation. The dashboard makes pairing easy, but Chrome controls installation.

### What The Status Badges Mean

| Badge | Meaning |
|---|---|
| Not installed | Chrome extension was not detected yet |
| Waiting for connection | Setup token exists, but extension has not connected yet |
| Installed but not connected | Extension was detected, but pairing is not complete |
| Connected | Extension registered successfully |
| Revoked | Device access was blocked by the gateway |

### If Something Does Not Work

| Problem | What To Try |
|---|---|
| Page will not load | Make sure the backend is running on `http://localhost:8000` |
| Login fails | Create a user at `/signup` or check your password |
| Chat says provider failed | Check model provider settings and API keys |
| Extension cannot connect | Generate a fresh setup token and paste the new connect URL |
| Token expired | Click **Refresh Token** on the extension setup page |
| Security Monitor looks empty | Send a chat request or extension request first |
| Revoked extension cannot send prompts | This is expected; reconnect with a new setup session if allowed |

### What To Remember

- Use **Secure Chat** for normal AI conversations.
- Use **Security Monitor** to see what is really happening.
- Use **Add Browser Extension** to connect Chrome.
- The extension stores only a gateway token and device id.
- Model API keys and gateway secrets stay on the backend.
- All allow/block decisions happen in the backend.

## Tech Stack

- Python 3.11+
- FastAPI + Uvicorn
- Pydantic v2
- SQLAlchemy async
- Alembic migrations
- SQLite with `aiosqlite` for local development
- PostgreSQL with `asyncpg` for Docker/production
- pytest + pytest-asyncio
- Server-rendered dashboard HTML/CSS/JS
- Chrome Manifest V3 extension

## Project Layout

```text
.
├── backend/
│   ├── app/
│   │   ├── core/       config, auth, database, monitoring, policy primitives
│   │   ├── models/     SQLAlchemy ORM models
│   │   ├── routers/    API routers
│   │   ├── schemas/    Pydantic request/response models
│   │   ├── services/   runtime, device, registry, gateway, firewall services
│   │   ├── testing/    self-test runner support
│   │   └── ui/         server-rendered dashboard pages
│   ├── alembic/        database migrations
│   ├── tests/          backend tests
│   └── requirements.txt
├── browser-extension/  Chrome MV3 extension source
├── frontend/           nginx proxy container
├── docs/               extra documentation
└── docker-compose.yml
```

## Quick Start: Local SQLite

```bash
cd backend
python3 -m venv ../.venv
source ../.venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Open:

- Dashboard: `http://localhost:8000/dashboard`
- Gateway Chat: `http://localhost:8000/dashboard/chat`
- Security Monitor: `http://localhost:8000/dashboard/security-monitor`
- Browser Extension Setup: `http://localhost:8000/dashboard/extension/install`
- API docs: `http://localhost:8000/docs`
- Health: `http://localhost:8000/health`

The default local database is `backend/dev.db` through `sqlite+aiosqlite:///./dev.db`.

## Quick Start: Docker

```bash
docker compose up --build
```

Services:

| Service | URL |
|---|---|
| Backend API + dashboard | `http://localhost:8000` |
| Frontend proxy | `http://localhost:3000` |
| PostgreSQL | `localhost:5432` |

The backend container runs:

```bash
alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000
```

The source is not volume-mounted in Docker, so rebuild the backend container after code changes.

## Environment Variables

Create `backend/.env` for local runs when needed.

```env
DATABASE_URL=sqlite+aiosqlite:///./dev.db
SECRET_KEY=change-me-in-production
DEBUG=false
ENVIRONMENT=development
AUTO_INIT_SCHEMA=false

ZTA_ENABLED=true
MODEL_RISK_ENABLED=true
PROMPT_ANALYSIS_ENABLED=true
RATE_LIMITING_ENABLED=true
USER_TRUST_SCORE_ENABLED=true

BACKEND_CORS_ORIGINS=http://localhost:3000,http://localhost:8000
FRONTEND_ORIGIN=http://localhost:8000
BROWSER_EXTENSION_ORIGIN_REGEX=^chrome-extension://[a-z]{32}$

OPENAI_API_KEY=
HF_TOKEN=
GATEWAY_API_KEYS=
DEFAULT_GATEWAY_API_KEY=

CHROME_EXTENSION_STORE_URL=
EXTENSION_ID=
PUBLIC_GATEWAY_API_URL=
```

For local PostgreSQL:

```env
DATABASE_URL=postgresql+asyncpg://appuser:apppass@localhost:5432/appdb
```

Then run:

```bash
docker compose up -d db
cd backend
alembic upgrade head
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

## Dashboard Pages

Canonical dashboard routes:

| Path | Purpose |
|---|---|
| `/dashboard` | Main dashboard |
| `/dashboard/chat` | Gateway Chat |
| `/dashboard/models` | Model registry and model management |
| `/dashboard/security-monitor` | SOC and security monitor |
| `/dashboard/policy` | Policy engine / security control plane |
| `/dashboard/research` | Research evaluation and comparisons |
| `/dashboard/account` | Account security |
| `/dashboard/extension/install` | Browser extension install/connect wizard |
| `/dashboard/extension/connect?token=...` | Extension pairing connect URL |
| `/downloads/browser-extension.zip` | Developer extension ZIP |

Several older paths redirect to these canonical routes, including `/chat`, `/models-manager`, `/research`, `/control-plane`, `/dashboard/soc`, and `/account-security`.

## Gateway Chat

Gateway Chat is the product core UI for secure chat usage.

- Chat sessions and messages are stored in the database.
- Full message history can be passed to model runtime routes.
- The UI is simplified into a main chat surface with a collapsible Zero Trust inspector.
- Dangerous controls are admin-restricted.
- Streaming is used where provider/runtime support exists.
- Failed provider execution is shown as gateway/provider failure rather than fake output.

Important routes:

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/v1/chat/sessions` | List user chat sessions |
| POST | `/api/v1/chat/sessions` | Create chat session |
| GET | `/api/v1/chat/sessions/{session_id}` | Load session and messages |
| PATCH | `/api/v1/chat/sessions/{session_id}` | Rename/archive session |
| DELETE | `/api/v1/chat/sessions/{session_id}` | Delete session |
| POST | `/api/v1/usage/infer` | Protected inference |
| POST | `/api/v1/usage/stream-infer` | Streaming inference path |

## Browser Extension Flow

The browser extension flow is designed to automate pairing while staying honest about Chrome’s installation rules.

Important truth: a normal website cannot silently install a Chrome extension. Chrome inline installation is disabled for normal websites. In production, users must go through the Chrome Web Store and confirm **Add to Chrome** there. The dashboard automates pairing, setup status, and connection detection, not Chrome’s installation confirmation.

### User Flow

1. User clicks **Add Browser Extension** in the dashboard.
2. The dashboard opens `/dashboard/extension/install`.
3. The backend creates a short-lived setup session and one-time pairing token.
4. Local/dev users can download the developer extension ZIP and load it unpacked.
5. Production users see **Add to Chrome**, which opens `CHROME_EXTENSION_STORE_URL`.
6. The dashboard checks whether the extension content script is installed.
7. The user opens the extension popup and pastes the connect URL.
8. The extension parses `gateway_api_url`, `pairing_token`, and `setup_session_id`.
9. The extension registers the device with the backend.
10. The dashboard polling updates to **Extension Connected** with device details.

### Extension API Routes

| Method | Path | Purpose |
|---|---|---|
| POST | `/api/v1/extension/pairing-token` | Existing compatibility endpoint for one-time pairing tokens |
| POST | `/api/v1/extension/setup-session` | Create automatic setup session and token |
| GET | `/api/v1/extension/setup-session/{setup_session_id}` | Poll setup-session status |
| POST | `/api/v1/extension/register-device` | Register extension device and issue gateway token |

### Extension Security

- Pairing tokens are tied to the authenticated user.
- Pairing tokens are hashed in the database.
- Pairing tokens expire quickly.
- Pairing tokens are one-time use and marked used after registration.
- The extension stores only the gateway-issued access token and `device_id`.
- The extension does not store model provider API keys.
- The extension does not store backend secrets.
- The extension is treated as untrusted client input.
- All security decisions remain in the backend.
- Extension tokens include device identity.
- Revoked devices are blocked by authenticated backend requests.
- Extension events are emitted to device/SOC logs with `source = browser_extension`.

### Development Install

```bash
cd backend
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Then:

1. Open `http://localhost:8000/dashboard/extension/install`.
2. Download the developer extension ZIP, or use the local `browser-extension/` folder.
3. Open `chrome://extensions`.
4. Enable **Developer Mode**.
5. Choose **Load unpacked**.
6. Select the `browser-extension/` folder.
7. Copy the dashboard connect URL into the extension popup.
8. Click **Connect**.

### Production Install

Set:

```env
CHROME_EXTENSION_STORE_URL=https://chromewebstore.google.com/detail/...
EXTENSION_ID=<published-extension-id>
PUBLIC_GATEWAY_API_URL=https://your-gateway.example.com
```

If `CHROME_EXTENSION_STORE_URL` is missing, the dashboard shows **Coming soon** instead of a broken install link.

## API Overview

All API routes use the `/api/v1` prefix.

### Authentication

| Method | Path | Purpose |
|---|---|---|
| POST | `/auth/signup` | Create user |
| POST | `/auth/token` | Log in and receive JWT |
| GET | `/auth/me` | Decode current token |
| GET | `/auth/me/profile` | Current user profile, trust, and rate state |
| POST | `/auth/logout` | Client-side logout message |
| POST | `/auth/me/change-password` | Change own password |
| POST | `/auth/admin/reset-password` | Admin password reset |

### Models

| Method | Path | Purpose |
|---|---|---|
| GET | `/models` | List accessible models |
| GET | `/models/runtime-readiness` | Runtime readiness summary |
| GET | `/models/my` | User-owned models |
| GET | `/models/{model_id}` | Model detail |
| POST | `/models` | Admin create model |
| PATCH | `/models/{model_id}` | Admin update model |
| DELETE | `/models/{model_id}` | Admin delete model |
| POST | `/models/user` | Create user-owned model |
| DELETE | `/models/user/{model_id}` | Delete own model |

### Inference, Detection, and Streaming

| Method | Path | Purpose |
|---|---|---|
| POST | `/detect` | Prompt/security detection |
| POST | `/detect/infer` | Detection plus inference path |
| POST | `/usage/infer` | Protected inference |
| POST | `/usage/stream-infer` | Streaming protected inference |

### Gateway and Firewall

| Method | Path | Purpose |
|---|---|---|
| POST | `/gateway/intercept` | Gateway interceptor for internal clients |
| POST | `/proxy/openai/chat/completions` | OpenAI-compatible proxy path |
| GET | `/firewall/clients` | List firewall clients |
| POST | `/firewall/clients` | Create firewall client |
| PATCH | `/firewall/clients/{client_id}` | Update firewall client |
| POST | `/firewall/proxy` | Firewall proxy inference |

### Devices and Sessions

| Method | Path | Purpose |
|---|---|---|
| GET | `/devices/me` | Current user devices |
| GET | `/devices/me/sessions` | Current user sessions |
| GET | `/devices/me/events` | Current user device/SOC events |
| GET | `/devices/me/current-info` | Browser/IP/OS context for current request |
| POST | `/devices/sessions/{session_id}/revoke` | Revoke own session |
| GET | `/devices/admin` | Admin list devices |
| GET | `/devices/admin/events` | Admin device/SOC events |
| POST | `/devices/{device_id}/trust` | Admin update trust |
| POST | `/devices/{device_id}/revoke` | Admin revoke device |

### Security and Research

| Method | Path | Purpose |
|---|---|---|
| GET | `/security/control-plane` | Security control-plane snapshot |
| GET | `/security/controls` | List controls |
| POST | `/security/controls` | Create control |
| PATCH | `/security/controls/{control_id}` | Update control |
| DELETE | `/security/controls/{control_id}` | Delete control |
| GET | `/security/detection-rules` | List detection rules |
| POST | `/security/detection-rules` | Create detection rule |
| PATCH | `/security/detection-rules/{rule_id}` | Update detection rule |
| DELETE | `/security/detection-rules/{rule_id}` | Delete detection rule |
| POST | `/security/policy/simulate` | Simulate policy decision |
| POST | `/security/test-suite` | Run security test-suite logic |
| POST | `/security/models/compare` | Compare model security posture |
| GET | `/research/evaluation-report` | Research report |
| GET | `/research/evaluation-dataset` | Evaluation dataset |
| GET | `/research/policy-replay` | Policy replay |
| GET | `/research/control-effectiveness` | Control effectiveness |
| GET | `/research/counterfactual-analysis` | Counterfactual analysis |
| GET | `/research/risk-drift` | Risk drift |
| GET | `/reporting/research-metrics` | Research metrics |

### Monitoring

| Method | Path | Purpose |
|---|---|---|
| GET | `/monitoring/zta/status` | ZTA state |
| POST | `/monitoring/zta/toggle` | Admin toggle ZTA |
| GET | `/monitoring/metrics` | Real request/model/security metrics |
| GET | `/monitoring/logs` | Admin request logs |
| GET | `/monitoring/logs/me` | Current user request logs |
| GET | `/monitoring/research/summary` | Research summary |
| GET | `/monitoring/users/{username}/trust` | User trust profile |
| GET | `/monitoring/users/trust/all` | Admin trust profiles |
| POST | `/monitoring/users/{username}/trust/reset` | Admin reset trust |
| GET | `/monitoring/users/{username}/trust/events` | Trust event history |
| GET | `/monitoring/models/{model_id}/posture/events` | Model posture events |
| GET | `/monitoring/users/{username}/rate` | User rate profile |
| GET | `/monitoring/users/rate/all` | Admin rate profiles |
| GET | `/monitoring/health` | Monitoring health |
| GET | `/monitoring/soc/attack-timeline` | SOC attack timeline |
| GET | `/monitoring/soc/user-anomalies` | SOC user anomalies |
| GET | `/monitoring/soc/threat-heatmap` | SOC threat heatmap |
| GET | `/monitoring/soc/alerts` | SOC alerts |

## Example API Calls

Create a user:

```bash
curl -X POST "http://localhost:8000/api/v1/auth/signup" \
  -H "Content-Type: application/json" \
  -d '{"email":"kira@example.com","username":"kira","password":"pass1234"}'
```

Log in:

```bash
curl -X POST "http://localhost:8000/api/v1/auth/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=kira&password=pass1234"
```

Run protected inference:

```bash
curl -X POST "http://localhost:8000/api/v1/usage/infer" \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "model_id": 1,
    "prompt": "Summarize this request",
    "messages": [{"role": "user", "content": "Summarize this request"}],
    "parameters": {"temperature": 0.2}
  }'
```

Create an extension setup session:

```bash
curl -X POST "http://localhost:8000/api/v1/extension/setup-session" \
  -H "Authorization: Bearer <TOKEN>"
```

Use the gateway interceptor:

```bash
curl -X POST "http://localhost:8000/api/v1/gateway/intercept" \
  -H "x-gateway-api-key: <GATEWAY_KEY>" \
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

## Database and Migrations

Use Alembic for schema changes:

```bash
cd backend
alembic upgrade head
```

Local development can use SQLite. Production should use PostgreSQL.

`AUTO_INIT_SCHEMA=false` is the normal setting. Some additive local table checks exist to keep development smoother, but migrations are the source of truth.

Recent data areas include:

- Chat sessions and messages
- Extension pairing/setup sessions
- Device and session records
- Request logs
- User trust events
- Model posture events
- Firewall clients
- Security controls and detection rules

## Testing

Run backend tests:

```bash
cd backend
pytest tests
```

Compile-check the backend:

```bash
cd backend
../.venv/bin/python -m compileall app
```

Check extension JavaScript and manifest:

```bash
node --check browser-extension/popup.js
node --check browser-extension/content.js
cd backend
../.venv/bin/python -m json.tool ../browser-extension/manifest.json
```

The dashboard also exposes a self-test route at `/dashboard/testing` through the research/testing area.

## Security Notes

- Do not commit real API keys, JWT secrets, database credentials, Hugging Face tokens, or OpenAI tokens.
- Replace `SECRET_KEY` before production.
- Use PostgreSQL for production.
- Keep `AUTO_INIT_SCHEMA=false` in production and run migrations explicitly.
- Restrict CORS to known frontend and extension origins.
- Put production extension install behind the Chrome Web Store listing.
- Do not put model provider keys or gateway secrets in the browser extension.
- Treat all extension requests as untrusted input.
- Rotate any secret exposed in logs, screenshots, commits, or shared environments.
- Review gateway API key and firewall client setup before exposing proxy endpoints publicly.
- Raw session tokens are not persisted; stored token references are hashed/truncated.

## Production Checklist

1. Set a strong `SECRET_KEY`.
2. Configure PostgreSQL with `DATABASE_URL`.
3. Run `alembic upgrade head`.
4. Set `PUBLIC_GATEWAY_API_URL` to the public HTTPS origin.
5. Set `FRONTEND_ORIGIN` and CORS origins.
6. Set `CHROME_EXTENSION_STORE_URL` and `EXTENSION_ID` after publishing the extension.
7. Configure gateway/firewall keys in env or DB-backed management.
8. Verify admin users and dangerous controls.
9. Confirm Security Monitor shows real logs after test traffic.
10. Confirm device revocation blocks extension requests.

## Development Notes

- Prefer existing backend routers, schemas, and services when adding features.
- Keep UI pages in `backend/app/ui/` consistent with the dark dashboard style.
- Use `/docs` to inspect live request/response schemas.
- Restart the backend after Python file changes unless running with `--reload`.
- Rebuild Docker images after code changes when using Docker Compose.
- Browser extension developer testing still requires Chrome Developer Mode.
