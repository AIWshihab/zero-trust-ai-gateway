from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import require_active_user
from app.models.attack_sequence_event import AttackSequenceEvent
from app.models.model import Model
from app.models.request_log import RequestLog
from app.models.security import DetectionRule, SecurityControl
from app.schemas import TokenData

router = APIRouter()


def _base_options(is_admin: bool) -> list[dict]:
    options = [
        {
            "id": "gateway_chat",
            "title": "Gateway Chat",
            "href": "/chat",
            "category": "user",
            "description": "Use registered AI models through protected chatbot conversations.",
            "summary": "ChatGPT-style model use with prompt guard, trust scoring, and audit logs.",
            "requires_admin": False,
        },
        {
            "id": "models",
            "title": "Model Registry",
            "href": "/models-manager",
            "category": "operations",
            "description": "Add, scan, protect, and disable OpenAI, Hugging Face, local, or custom models.",
            "summary": "Model onboarding, provider metadata, posture scanning, and deletion.",
            "requires_admin": True,
        },
        {
            "id": "control_plane",
            "title": "Control Plane",
            "href": "/control-plane",
            "category": "security",
            "description": "Manage OWASP LLM controls and dynamic detection rules.",
            "summary": "LLM01-LLM10 controls, prompt/output rules, and policy simulation.",
            "requires_admin": True,
        },
        {
            "id": "audit_logs",
            "title": "Audit Logs",
            "href": "/logs",
            "category": "monitoring",
            "description": "Review gateway request logs, decisions, risks, and enforcement outcomes.",
            "summary": "Request audit trail for investigations and compliance evidence.",
            "requires_admin": True,
        },
        {
            "id": "research",
            "title": "Research Evaluation",
            "href": "/research",
            "category": "research",
            "description": "View policy replay, counterfactuals, control effectiveness, and risk drift.",
            "summary": "Dissertation-ready evaluation layer for the gateway.",
            "requires_admin": True,
        },
        {
            "id": "soc_dashboard",
            "title": "SOC Dashboard",
            "href": "/dashboard/soc",
            "category": "monitoring",
            "description": "Live security operations dashboard for attack timelines, anomalies, heatmaps, and alerts.",
            "summary": "Operational SOC view over real gateway telemetry.",
            "requires_admin": True,
        },
        {
            "id": "firewall_clients",
            "title": "Firewall Clients",
            "href": "/dashboard/firewall",
            "category": "security",
            "description": "Manage external firewall clients, API keys, trust posture, and rate limits.",
            "summary": "Client-level PEP governance for external app access.",
            "requires_admin": True,
        },
        {
            "id": "model_compare",
            "title": "Model Compare",
            "href": "/dashboard/models/compare",
            "category": "analysis",
            "description": "Compare model decisions and safety outcomes for the same prompt.",
            "summary": "Side-by-side model risk and policy outcomes.",
            "requires_admin": False,
        },
        {
            "id": "security_tests",
            "title": "Security Tests",
            "href": "/dashboard/security",
            "category": "security",
            "description": "Run the built-in AI attack simulation suite and review effectiveness metrics.",
            "summary": "Detection accuracy, false positive rate, and per-test outcomes.",
            "requires_admin": False,
        },
        {
            "id": "demo_evaluation",
            "title": "Evaluation Demo",
            "href": "/dashboard/demo",
            "category": "research",
            "description": "Replay attack scenarios and present policy impact using existing gateway evidence.",
            "summary": "Scenario timeline, policy impact, control effectiveness, system flow, and export.",
            "requires_admin": False,
        },
        {
            "id": "evaluation_system",
            "title": "Evaluation System",
            "href": "/dashboard/evaluation",
            "category": "research",
            "description": "Compare deterministic baseline behavior against gateway decisions from existing logs.",
            "summary": "Baseline vs gateway metrics, attack progression, policy impact, and report export.",
            "requires_admin": False,
        },
        {
            "id": "self_testing",
            "title": "System Self-Test",
            "href": "/dashboard/testing",
            "category": "monitoring",
            "description": "Run SOC endpoint test harness and inspect pass/fail health inside the UI.",
            "summary": "On-demand pytest wrapper output for operational confidence.",
            "requires_admin": True,
        },
    ]
    return [item for item in options if is_admin or not item["requires_admin"]]


@router.get("/options")
async def navigation_options(
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(require_active_user),
):
    is_admin = "admin" in (current_user.scopes or [])
    model_count = int((await db.execute(select(func.count(Model.id)).where(Model.is_active.is_(True)))).scalar_one() or 0)
    control_count = int((await db.execute(select(func.count(SecurityControl.id)).where(SecurityControl.enabled.is_(True)))).scalar_one() or 0)
    rule_count = int((await db.execute(select(func.count(DetectionRule.id)).where(DetectionRule.enabled.is_(True)))).scalar_one() or 0)
    log_count = int((await db.execute(select(func.count(RequestLog.id)))).scalar_one() or 0)
    attack_count = int((await db.execute(select(func.count(AttackSequenceEvent.id)))).scalar_one() or 0)

    return {
        "user": {
            "username": current_user.username,
            "email": current_user.email,
            "scopes": current_user.scopes,
            "is_admin": is_admin,
        },
        "overview": {
            "active_models": model_count,
            "enabled_controls": control_count,
            "enabled_detection_rules": rule_count,
            "request_logs": log_count,
            "attack_sequence_events": attack_count,
        },
        "options": _base_options(is_admin),
    }
