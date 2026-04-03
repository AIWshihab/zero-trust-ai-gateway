from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy import select, func, case
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import require_active_user, require_admin
from app.models.request_log import RequestLog
from app.schemas import TokenData, RequestDecision
from app.core.trust_score import (
    get_trust_profile,
    get_all_trust_profiles,
    reset_trust_score,
)
from app.core.rate_limiter import (
    get_rate_profile,
    get_all_rate_profiles,
)
from app.core.config import get_settings
import os

router = APIRouter()


@router.post("/zta/toggle")
async def toggle_zta(
    current_user: TokenData = Depends(require_admin),
):
    settings = get_settings()
    current = settings.ZTA_ENABLED

    os.environ["ZTA_ENABLED"] = str(not current).upper()
    get_settings.cache_clear()

    new_state = get_settings().ZTA_ENABLED
    return {
        "previous_state": current,
        "new_state": new_state,
        "message": f"ZTA {'enabled' if new_state else 'disabled'}",
    }


@router.get("/zta/status")
async def zta_status(
    current_user: TokenData = Depends(require_active_user),
):
    return {
        "zta_enabled": get_settings().ZTA_ENABLED,
        "message": "ZTA is active" if get_settings().ZTA_ENABLED else "⚠️ ZTA is disabled — no security enforcement",
    }


@router.get("/metrics")
async def metrics_summary(
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(require_active_user),
):
    query = select(
        func.count(RequestLog.id).label("total_requests"),
        func.sum(case((RequestLog.decision == "block", 1), else_=0)).label("blocked_requests"),
        func.sum(case((RequestLog.decision == "challenge", 1), else_=0)).label("challenged_requests"),
        func.sum(case((RequestLog.decision == "allow", 1), else_=0)).label("allowed_requests"),
        func.avg(RequestLog.security_score).label("avg_security_score"),
        func.avg(RequestLog.latency_ms).label("avg_latency_ms"),
    )

    result = await db.execute(query)
    row = result.one()

    total_requests = int(row.total_requests or 0)
    blocked_requests = int(row.blocked_requests or 0)
    challenged_requests = int(row.challenged_requests or 0)
    allowed_requests = int(row.allowed_requests or 0)
    avg_security_score = round(float(row.avg_security_score or 0.0), 4)
    avg_latency_ms = round(float(row.avg_latency_ms or 0.0), 2)
    block_rate = round((blocked_requests / total_requests) * 100, 2) if total_requests else 0.0

    return {
        "total_requests": total_requests,
        "blocked_requests": blocked_requests,
        "challenged_requests": challenged_requests,
        "allowed_requests": allowed_requests,
        "avg_security_score": avg_security_score,
        "avg_latency_ms": avg_latency_ms,
        "block_rate": block_rate,
    }


@router.get("/logs")
async def all_logs(
    limit: int = Query(default=50, le=500),
    decision: RequestDecision | None = Query(default=None),
    model_id: int | None = Query(default=None),
    current_user: TokenData = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    query = select(RequestLog)

    if decision is not None:
        decision_value = decision.value if hasattr(decision, "value") else str(decision)
        query = query.where(RequestLog.decision == decision_value)

    if model_id is not None:
        query = query.where(RequestLog.model_id == model_id)

    query = query.order_by(RequestLog.timestamp.desc()).limit(limit)

    result = await db.execute(query)
    rows = result.scalars().all()

    logs = [
        {
            "id": row.id,
            "user_id": row.user_id,
            "model_id": row.model_id,
            "prompt_hash": row.prompt_hash,
            "security_score": row.security_score,
            "prompt_risk_score": row.prompt_risk_score,
            "output_risk_score": row.output_risk_score,
            "decision": row.decision,
            "blocked": row.blocked,
            "secure_mode_enabled": row.secure_mode_enabled,
            "reason": row.reason,
            "latency_ms": row.latency_ms,
            "timestamp": row.timestamp.isoformat() if row.timestamp else None,
        }
        for row in rows
    ]

    return {
        "total": len(logs),
        "limit": limit,
        "logs": logs,
    }


@router.get("/logs/me")
async def my_logs(
    current_user: TokenData = Depends(require_active_user),
    db: AsyncSession = Depends(get_db),
):
    # Request logs are keyed by numeric user_id.
    # If user_id is missing in token, return safely without leaking data.
    user_id = getattr(current_user, "user_id", None)

    if user_id is None:
        return {
            "username": current_user.username,
            "total": 0,
            "logs": [],
        }

    query = (
        select(RequestLog)
        .where(RequestLog.user_id == user_id)
        .order_by(RequestLog.timestamp.desc())
        .limit(200)
    )

    result = await db.execute(query)
    rows = result.scalars().all()

    logs = [
        {
            "id": row.id,
            "user_id": row.user_id,
            "model_id": row.model_id,
            "prompt_hash": row.prompt_hash,
            "security_score": row.security_score,
            "prompt_risk_score": row.prompt_risk_score,
            "output_risk_score": row.output_risk_score,
            "decision": row.decision,
            "blocked": row.blocked,
            "secure_mode_enabled": row.secure_mode_enabled,
            "reason": row.reason,
            "latency_ms": row.latency_ms,
            "timestamp": row.timestamp.isoformat() if row.timestamp else None,
        }
        for row in rows
    ]

    return {
        "username": current_user.username,
        "total": len(logs),
        "logs": logs,
    }


@router.get("/users/{username}/trust")
async def user_trust_profile(
    username: str,
    current_user: TokenData = Depends(require_active_user),
):
    if current_user.username != username and "admin" not in current_user.scopes:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view your own trust profile",
        )
    return get_trust_profile(username)


@router.get("/users/trust/all")
async def all_trust_profiles(
    current_user: TokenData = Depends(require_admin),
):
    return get_all_trust_profiles()


@router.post("/users/{username}/trust/reset")
async def reset_user_trust(
    username: str,
    current_user: TokenData = Depends(require_admin),
):
    new_score = reset_trust_score(username)
    return {
        "message": f"Trust score reset for {username}",
        "new_score": new_score,
    }


@router.get("/users/{username}/rate")
async def user_rate_profile(
    username: str,
    current_user: TokenData = Depends(require_active_user),
):
    if current_user.username != username and "admin" not in current_user.scopes:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view your own rate profile",
        )
    return get_rate_profile(username)


@router.get("/users/rate/all")
async def all_rate_profiles(
    current_user: TokenData = Depends(require_admin),
):
    return get_all_rate_profiles()


@router.get("/health")
async def monitoring_health(
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(require_active_user),
):
    query = select(
        func.count(RequestLog.id).label("total_requests"),
        func.sum(case((RequestLog.decision == "block", 1), else_=0)).label("blocked_requests"),
        func.sum(case((RequestLog.decision == "challenge", 1), else_=0)).label("challenged_requests"),
        func.sum(case((RequestLog.decision == "allow", 1), else_=0)).label("allowed_requests"),
        func.avg(RequestLog.security_score).label("avg_security_score"),
        func.avg(RequestLog.latency_ms).label("avg_latency_ms"),
    )

    result = await db.execute(query)
    row = result.one()

    total_requests = int(row.total_requests or 0)
    blocked_requests = int(row.blocked_requests or 0)
    challenged_requests = int(row.challenged_requests or 0)
    allowed_requests = int(row.allowed_requests or 0)
    avg_security_score = round(float(row.avg_security_score or 0.0), 4)
    avg_latency_ms = round(float(row.avg_latency_ms or 0.0), 2)
    block_rate = round((blocked_requests / total_requests) * 100, 2) if total_requests else 0.0

    rate_profiles = get_all_rate_profiles()
    active_users = [r for r in rate_profiles if r["requests_in_window"] > 0]

    return {
        "metrics": {
            "total_requests": total_requests,
            "blocked_requests": blocked_requests,
            "challenged_requests": challenged_requests,
            "allowed_requests": allowed_requests,
            "avg_security_score": avg_security_score,
            "avg_latency_ms": avg_latency_ms,
            "block_rate": block_rate,
        },
        "active_users": len(active_users),
        "flagged_users": [
            r for r in active_users if r["is_rate_limited"]
        ],
    }
