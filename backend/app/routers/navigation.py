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
            "href": "/dashboard#research",
            "category": "research",
            "description": "View policy replay, counterfactuals, control effectiveness, and risk drift.",
            "summary": "Dissertation-ready evaluation layer for the gateway.",
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
