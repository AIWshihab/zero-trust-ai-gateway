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
            "id": "secure_chat",
            "title": "Secure AI Inference",
            "href": "/dashboard/chat",
            "category": "inference",
            "description": "Send prompts through the behaviour-aware Zero Trust gateway and inspect the decision, risk score, explanation trace, and output guard result.",
            "summary": "Primary workflow for Behaviour-Aware Secure AI Inference.",
            "requires_admin": False,
        },
        {
            "id": "models",
            "title": "Model Registry & Readiness",
            "href": "/dashboard/models",
            "category": "model management",
            "description": "Register owned model endpoints, inspect readiness, and review model security posture before inference is allowed.",
            "summary": "User-owned model management with admin visibility across all registered models.",
            "requires_admin": False,
        },
        {
            "id": "security_monitor",
            "title": "Security Observability",
            "href": "/dashboard/security-monitor",
            "category": "observability",
            "description": "Inspect recent allow, challenge, and block decisions with user trust changes, model risk events, and decision traces.",
            "summary": "Security visibility for AI inference decisions without unnecessary operational clutter.",
            "requires_admin": False,
        },
        {
            "id": "policy_engine",
            "title": "Explainable Policy Engine",
            "href": "/dashboard/policy",
            "category": "policy",
            "description": "Review active policy mode, thresholds, enabled controls, detection rules, secure mode, and output guard settings.",
            "summary": "Deterministic policy logic with admin-only editing and user-visible explanation where appropriate.",
            "requires_admin": False,
        },
        {
            "id": "research",
            "title": "Replayable Security Evaluation",
            "href": "/dashboard/research",
            "category": "research",
            "description": "Run test suites, policy replay, counterfactuals, model comparison, and control-effectiveness analysis from audit evidence.",
            "summary": "Users evaluate their own evidence; admins can run global evaluation and exports.",
            "requires_admin": False,
        },
        {
            "id": "account_security",
            "title": "Account",
            "href": "/dashboard/account",
            "category": "trust",
            "description": "View profile, role, trust state, owned models, API usage summary, and recent security outcomes.",
            "summary": "Simple account and trust posture view.",
            "requires_admin": False,
        },
    ]
    return [item for item in options if is_admin or not item["requires_admin"]]


def _admin_option_count() -> int:
    return sum(1 for item in _base_options(True) if item["requires_admin"])


@router.get("/options")
async def navigation_options(
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(require_active_user),
):
    is_admin = "admin" in (current_user.scopes or [])
    model_count = int((await db.execute(select(func.count(Model.id)).where(Model.is_active.is_(True)))).scalar_one() or 0)
    control_count = int((await db.execute(select(func.count(SecurityControl.id)).where(SecurityControl.enabled.is_(True)))).scalar_one() or 0)
    rule_count = int((await db.execute(select(func.count(DetectionRule.id)).where(DetectionRule.enabled.is_(True)))).scalar_one() or 0)
    log_count = int((await db.execute(select(func.count(RequestLog.id)).where(RequestLog.user_id == current_user.user_id))).scalar_one() or 0)
    attack_count = int((await db.execute(select(func.count(AttackSequenceEvent.id)).where(AttackSequenceEvent.user_id == current_user.user_id))).scalar_one() or 0)

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
            "admin_option_count": _admin_option_count(),
        },
        "options": _base_options(is_admin),
    }
