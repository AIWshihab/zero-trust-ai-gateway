from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.database import AsyncSessionLocal, init_db
from app.routers import auth, models, detect, assessment, protection, usage, reporting, security, research, navigation
from app.core import monitoring
from app.services.security_catalog import seed_default_security_controls
from app.ui.control_plane import CONTROL_PLANE_HTML
from app.ui.chat import CHAT_HTML
from app.ui.dashboard import DASHBOARD_HTML
from app.ui.login import LOGIN_HTML
from app.ui.logs import LOGS_HTML
from app.ui.model_manager import MODEL_MANAGER_HTML
from app.ui.signup import SIGNUP_HTML

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    async with AsyncSessionLocal() as db:
        await seed_default_security_controls(db)
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

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ALLOW_ORIGINS,
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
    research.router,
    prefix=f"{settings.API_V1_PREFIX}/research",
    tags=["Research Evaluation"],
)

app.include_router(
    navigation.router,
    prefix=f"{settings.API_V1_PREFIX}/navigation",
    tags=["Navigation"],
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


@app.get("/chat", response_class=HTMLResponse, tags=["Dashboard"])
async def chat_page():
    return CHAT_HTML


@app.get("/control-plane", response_class=HTMLResponse, tags=["Dashboard"])
async def control_plane_page():
    return CONTROL_PLANE_HTML


@app.get("/models-manager", response_class=HTMLResponse, tags=["Dashboard"])
async def models_manager_page():
    return MODEL_MANAGER_HTML


@app.get("/logs", response_class=HTMLResponse, tags=["Dashboard"])
async def logs_page():
    return LOGS_HTML


@app.get("/signup", response_class=HTMLResponse, tags=["Dashboard"])
async def signup_page():
    return SIGNUP_HTML
