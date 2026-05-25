import logging
import os
import tempfile
import zipfile
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.background import BackgroundTask

from app.core.config import get_settings
from app.core.database import AsyncSessionLocal, init_additive_security_tables, init_db
from app.routers import auth, models, detect, assessment, protection, usage, reporting, security, research, navigation, gateway, firewall, evaluation, testing, system, devices, streaming, chat, extension
from app.core import monitoring
from app.services.security_catalog import seed_default_security_controls
from app.services.firewall_clients import seed_default_firewall_client
from app.services.seed_models import seed_preset_models
from app.ui.control_plane import CONTROL_PLANE_HTML
from app.ui.chat import CHAT_HTML
from app.ui.dashboard import DASHBOARD_HTML
from app.ui.login import LOGIN_HTML
from app.ui.logs import LOGS_HTML
from app.ui.model_manager import MODEL_MANAGER_HTML
from app.ui.model_compare import MODEL_COMPARE_HTML
from app.ui.research import RESEARCH_HTML
from app.ui.security_suite import SECURITY_SUITE_HTML
from app.ui.soc_dashboard import SOC_DASHBOARD_HTML
from app.ui.firewall_admin import FIREWALL_ADMIN_HTML
from app.ui.demo_dashboard import DEMO_DASHBOARD_HTML
from app.ui.evaluation_dashboard import EVALUATION_DASHBOARD_HTML
from app.ui.testing_dashboard import TESTING_DASHBOARD_HTML
from app.ui.signup import SIGNUP_HTML
from app.ui.gt_mode import GT_MODE_HTML
from app.ui.control_center import CONTROL_CENTER_HTML
from app.ui.account_security import ACCOUNT_SECURITY_HTML
from app.ui.my_models import MY_MODELS_HTML
from app.ui.my_devices import MY_DEVICES_HTML
from app.ui.extension import EXTENSION_HTML
from app.ui.extension_connect import EXTENSION_CONNECT_HTML
from app.ui.getting_started import GETTING_STARTED_HTML

settings = get_settings()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    await init_additive_security_tables()
    async with AsyncSessionLocal() as db:
        await seed_default_security_controls(db)
        await seed_default_firewall_client(db)
        await seed_preset_models(db)
    logger.info("Application database dialect: %s", settings.DATABASE_DIALECT)
    print(f"🚀 Starting {settings.APP_NAME}")
    yield
    print("🛑 Shutting down gateway")


app = FastAPI(
    title=settings.APP_NAME,
    description="Dynamic Zero-Trust Architecture for Secure AI Model Serving",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

_cors_origins = list(settings.CORS_ALLOW_ORIGINS)
if settings.FRONTEND_ORIGIN and settings.FRONTEND_ORIGIN not in _cors_origins:
    _cors_origins.append(settings.FRONTEND_ORIGIN)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_origin_regex=settings.BROWSER_EXTENSION_ORIGIN_REGEX,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(
    auth.router,
    prefix=f"{settings.API_V1_PREFIX}/auth",
    tags=["Authentication"],
)

app.include_router(
    models.router,
    prefix=f"{settings.API_V1_PREFIX}/models",
    tags=["Model Registry"],
)

app.include_router(
    detect.router,
    prefix=f"{settings.API_V1_PREFIX}/detect",
    tags=["Detection & Policy"],
)

app.include_router(
    assessment.router,
    prefix=f"{settings.API_V1_PREFIX}/assessment",
    tags=["Assessment"],
)

app.include_router(
    protection.router,
    prefix=f"{settings.API_V1_PREFIX}/protection",
    tags=["Protection"],
)

app.include_router(
    usage.router,
    prefix=f"{settings.API_V1_PREFIX}/usage",
    tags=["Usage"],
)

app.include_router(
    streaming.router,
    prefix=f"{settings.API_V1_PREFIX}/usage",
    tags=["Usage"],
)

app.include_router(
    chat.router,
    prefix=f"{settings.API_V1_PREFIX}/chat",
    tags=["Gateway Chat"],
)

app.include_router(
    extension.router,
    prefix=f"{settings.API_V1_PREFIX}/extension",
    tags=["Browser Extension"],
)

app.include_router(
    gateway.router,
    prefix=settings.API_V1_PREFIX,
    tags=["AI Firewall / API Interceptor"],
)

app.include_router(
    firewall.router,
    prefix=f"{settings.API_V1_PREFIX}/firewall",
    tags=["Adaptive AI Firewall PEP"],
)

app.include_router(
    reporting.router,
    prefix=f"{settings.API_V1_PREFIX}/reporting",
    tags=["Reporting"],
)

app.include_router(
    security.router,
    prefix=f"{settings.API_V1_PREFIX}/security",
    tags=["AI Security Control Plane"],
)

app.include_router(
    monitoring.router,
    prefix=f"{settings.API_V1_PREFIX}/monitoring",
    tags=["Monitoring"],
)

app.include_router(
    evaluation.router,
    prefix=f"{settings.API_V1_PREFIX}/evaluation",
    tags=["Evaluation"],
)

app.include_router(
    testing.router,
    prefix=f"{settings.API_V1_PREFIX}/testing",
    tags=["Testing"],
)

app.include_router(
    research.router,
    prefix=f"{settings.API_V1_PREFIX}/research",
    tags=["Research Evaluation"],
)

app.include_router(
    navigation.router,
    prefix=f"{settings.API_V1_PREFIX}/navigation",
    tags=["Navigation"],
)

app.include_router(
    system.router,
    prefix=f"{settings.API_V1_PREFIX}/system",
    tags=["System State"],
)

app.include_router(
    devices.router,
    prefix=f"{settings.API_V1_PREFIX}/devices",
    tags=["Device & Session Intelligence"],
)


@app.get("/health", tags=["Health"])
async def health_check():
    return {
        "status": "online",
        "app": settings.APP_NAME,
        "version": "1.0.0",
    }


@app.get("/", tags=["Root"])
async def root():
    return RedirectResponse(url="/login")


@app.get("/login", response_class=HTMLResponse, tags=["Dashboard"])
async def login_page():
    return LOGIN_HTML


@app.get("/dashboard", response_class=HTMLResponse, tags=["Dashboard"])
async def dashboard():
    return DASHBOARD_HTML


@app.get("/dashboard/getting-started", response_class=HTMLResponse, tags=["Dashboard"])
async def getting_started_page():
    return GETTING_STARTED_HTML


@app.get("/chat", response_class=HTMLResponse, tags=["Dashboard"])
async def chat_page():
    return RedirectResponse(url="/dashboard/chat")


@app.get("/dashboard/chat", response_class=HTMLResponse, tags=["Dashboard"])
async def secure_chat_page():
    return CHAT_HTML


@app.get("/dashboard/extension", response_class=HTMLResponse, tags=["Dashboard"])
async def browser_extension_page():
    return RedirectResponse(url="/dashboard/extension/install")


@app.get("/dashboard/extension/install", response_class=HTMLResponse, tags=["Dashboard"])
async def browser_extension_install_page():
    return EXTENSION_HTML


@app.get("/dashboard/extension/connect", response_class=HTMLResponse, tags=["Dashboard"])
async def browser_extension_connect_page():
    return EXTENSION_CONNECT_HTML


@app.get("/downloads/browser-extension.zip", tags=["Dashboard"])
async def download_browser_extension():
    source_dir = Path(__file__).resolve().parents[2] / "browser-extension"
    if not source_dir.exists():
        return RedirectResponse(url="/dashboard/extension")

    fd, archive_path = tempfile.mkstemp(prefix="browser-extension-", suffix=".zip")
    os.close(fd)
    Path(archive_path).unlink(missing_ok=True)
    with zipfile.ZipFile(archive_path, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in source_dir.rglob("*"):
            if path.is_file():
                archive.write(path, path.relative_to(source_dir.parent))
    return FileResponse(
        archive_path,
        filename="zero-trust-ai-gateway-browser-extension.zip",
        media_type="application/zip",
        background=BackgroundTask(lambda: Path(archive_path).unlink(missing_ok=True)),
    )


@app.get("/control-plane", response_class=HTMLResponse, tags=["Dashboard"])
async def control_plane_page():
    return RedirectResponse(url="/dashboard/policy")


@app.get("/dashboard/policy", response_class=HTMLResponse, tags=["Dashboard"])
async def policy_engine_page():
    return CONTROL_PLANE_HTML


@app.get("/models-manager", response_class=HTMLResponse, tags=["Dashboard"])
async def models_manager_page():
    return RedirectResponse(url="/dashboard/models")


@app.get("/my-models", response_class=HTMLResponse, tags=["Dashboard"])
async def my_models_page():
    return RedirectResponse(url="/dashboard/models")


@app.get("/dashboard/models", response_class=HTMLResponse, tags=["Dashboard"])
async def unified_models_page():
    return MODEL_MANAGER_HTML


@app.get("/logs", response_class=HTMLResponse, tags=["Dashboard"])
async def logs_page():
    return LOGS_HTML


@app.get("/research", response_class=HTMLResponse, tags=["Dashboard"])
async def research_page():
    return RedirectResponse(url="/dashboard/research")


@app.get("/dashboard/research", response_class=HTMLResponse, tags=["Dashboard"])
async def research_evaluation_page():
    return RESEARCH_HTML


@app.get("/dashboard/soc", response_class=HTMLResponse, tags=["Dashboard"])
async def soc_dashboard_page():
    return RedirectResponse(url="/dashboard/security-monitor")


@app.get("/dashboard/security-monitor", response_class=HTMLResponse, tags=["Dashboard"])
async def security_monitor_page():
    return SOC_DASHBOARD_HTML


@app.get("/dashboard/firewall", response_class=HTMLResponse, tags=["Dashboard"])
async def firewall_dashboard_page():
    return RedirectResponse(url="/dashboard/policy")


@app.get("/dashboard/models/compare", response_class=HTMLResponse, tags=["Dashboard"])
async def model_compare_page():
    return RedirectResponse(url="/dashboard/research?tab=model-comparison")


@app.get("/dashboard/compare", response_class=HTMLResponse, tags=["Dashboard"])
async def old_compare_page():
    return RedirectResponse(url="/dashboard/research?tab=model-comparison")


@app.get("/dashboard/registry", response_class=HTMLResponse, tags=["Dashboard"])
async def old_registry_page():
    return RedirectResponse(url="/dashboard/models")


@app.get("/dashboard/security", response_class=HTMLResponse, tags=["Dashboard"])
async def security_suite_page():
    return RedirectResponse(url="/dashboard/research?tab=test-suite")


@app.get("/dashboard/tests", response_class=HTMLResponse, tags=["Dashboard"])
async def old_tests_page():
    return RedirectResponse(url="/dashboard/research?tab=test-suite")


@app.get("/dashboard/demo", response_class=HTMLResponse, tags=["Dashboard"])
async def demo_dashboard_page():
    return RedirectResponse(url="/dashboard")


@app.get("/dashboard/evaluation", response_class=HTMLResponse, tags=["Dashboard"])
async def evaluation_dashboard_page():
    return RedirectResponse(url="/dashboard/research")


@app.get("/dashboard/evaluate", response_class=HTMLResponse, tags=["Dashboard"])
async def old_evaluate_page():
    return RedirectResponse(url="/dashboard/research")


@app.get("/dashboard/testing", response_class=HTMLResponse, tags=["Dashboard"])
async def testing_dashboard_page():
    return RedirectResponse(url="/dashboard/research?tab=test-suite")


@app.get("/dashboard/self-test", response_class=HTMLResponse, tags=["Dashboard"])
async def old_self_test_page():
    return RedirectResponse(url="/dashboard/research?tab=test-suite")


@app.get("/signup", response_class=HTMLResponse, tags=["Dashboard"])
async def signup_page():
    return SIGNUP_HTML


@app.get("/gt-mode", response_class=HTMLResponse, tags=["Dashboard"])
async def gt_mode_page():
    return RedirectResponse(url="/dashboard")


@app.get("/dashboard/gt-mode", response_class=HTMLResponse, tags=["Dashboard"])
async def old_gt_mode_page():
    return RedirectResponse(url="/dashboard")


@app.get("/control-center", response_class=HTMLResponse, tags=["Dashboard"])
async def control_center_page():
    return RedirectResponse(url="/dashboard/policy")


@app.get("/dashboard/control", response_class=HTMLResponse, tags=["Dashboard"])
async def old_control_page():
    return RedirectResponse(url="/dashboard/policy")


@app.get("/account-security", response_class=HTMLResponse, tags=["Dashboard"])
async def account_security_page():
    return RedirectResponse(url="/dashboard/account")


@app.get("/dashboard/account", response_class=HTMLResponse, tags=["Dashboard"])
async def account_page():
    return ACCOUNT_SECURITY_HTML


@app.get("/my-devices", response_class=HTMLResponse, tags=["Dashboard"])
async def my_devices_page():
    return MY_DEVICES_HTML
