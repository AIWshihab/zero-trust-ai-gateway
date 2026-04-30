from datetime import datetime, timezone
import os

from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy import select, func, case
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import require_active_user, require_admin
from app.models.model import Model
from app.models.model_posture_event import ModelPostureEvent
from app.models.request_log import RequestLog
from app.models.user import User
from app.models.user_trust_event import UserTrustEvent
from app.schemas import TokenData, RequestDecision
from app.core.rate_limiter import (
    get_rate_profile,
    get_all_rate_profiles,
)
from app.core.config import get_settings
from app.services.reassessment_service import (
    get_trust_profile_persistent,
    list_trust_profiles_persistent,
    reset_user_trust_persistent,
)
from app.services.threat_intelligence import get_user_attack_sequence_summary

router = APIRouter()
_MONITORING_STARTED_AT = datetime.now(timezone.utc)
_ZTA_LAST_UPDATED_AT = datetime.now(timezone.utc)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(dt: datetime | None) -> str | None:
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.isoformat()


def _zta_mode(enabled: bool) -> str:
    return "strict" if enabled else "permissive"


def _zta_payload(*, enabled: bool, previous_state: bool | None = None) -> dict:
    payload = {
        "enabled": bool(enabled),
        "zta_enabled": bool(enabled),
        "mode": _zta_mode(bool(enabled)),
        "last_updated": _iso(_ZTA_LAST_UPDATED_AT),
        "message": "ZTA is active" if enabled else "⚠️ ZTA is disabled — no security enforcement",
    }
    if previous_state is not None:
        payload["previous_state"] = bool(previous_state)
        payload["new_state"] = bool(enabled)
    return payload


def _safe_float(value, default: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:
        return float(default)


def _coerce_int(value, default: int = 0) -> int:
    try:
        return int(value)
    except Exception:
        return int(default)


def _normalize_rate_profile(raw: dict) -> dict:
    username = str(raw.get("username") or "unknown")
    requests_in_window = _safe_float(raw.get("requests_in_window"), 0.0)
    window_seconds = max(1.0, _safe_float(raw.get("window_seconds"), 60.0))
    limit = max(1.0, _safe_float(raw.get("limit"), 1.0))

    requests_per_minute = (requests_in_window / window_seconds) * 60.0
    requests_per_hour = (requests_in_window / window_seconds) * 3600.0
    limit_per_minute = (limit / window_seconds) * 60.0
    limit_per_hour = (limit / window_seconds) * 3600.0

    return {
        # Canonical fields for frontend contract.
        "user_id": username,
        "username": username,
        "requests_per_minute": round(requests_per_minute, 2),
        "limit_per_minute": round(limit_per_minute, 2),
        "requests_per_hour": round(requests_per_hour, 2),
        "limit_per_hour": round(limit_per_hour, 2),
        # Backward-compatible fields.
        "requests_in_window": _coerce_int(requests_in_window),
        "window_seconds": _coerce_int(window_seconds, 60),
        "limit": _coerce_int(limit, 1),
        "rate_score": _safe_float(raw.get("rate_score"), 0.0),
        "is_rate_limited": bool(raw.get("is_rate_limited", False)),
        "abuse_strikes": _coerce_int(raw.get("abuse_strikes"), 0),
        "penalty_active": bool(raw.get("penalty_active", False)),
        "cooldown_remaining_seconds": _coerce_int(raw.get("cooldown_remaining_seconds"), 0),
        "last_penalty_reason": raw.get("last_penalty_reason"),
    }


async def _build_enriched_trust_profile(
    db: AsyncSession,
    *,
    username: str,
    base_profile: dict,
    recent_limit: int = 3,
) -> dict:
    user = (await db.execute(select(User).where(User.username == username))).scalar_one_or_none()
    if user is None:
        return {
            "user_id": username,
            "username": username,
            "trust_score": _safe_float(base_profile.get("trust_score"), 0.0),
            "trust_penalty": _safe_float(base_profile.get("trust_penalty"), 0.0),
            "trust_level": str(base_profile.get("trust_level") or "unknown"),
            "total_requests": 0,
            "blocked_requests": 0,
            "challenged_requests": 0,
            "last_activity": None,
            "recent_changes": [],
        }

    stats_query = select(
        func.count(RequestLog.id).label("total_requests"),
        func.sum(case((RequestLog.decision == "block", 1), else_=0)).label("blocked_requests"),
        func.sum(case((RequestLog.decision == "challenge", 1), else_=0)).label("challenged_requests"),
        func.max(RequestLog.timestamp).label("last_activity"),
    ).where(RequestLog.user_id == user.id)
    stats_row = (await db.execute(stats_query)).one()

    trust_events = (
        await db.execute(
            select(UserTrustEvent)
            .where(UserTrustEvent.user_id == user.id)
            .order_by(UserTrustEvent.timestamp.desc())
            .limit(max(1, recent_limit))
        )
    ).scalars().all()

    recent_changes = []
    for event in trust_events:
        previous = _safe_float(event.previous_value, _safe_float(event.new_value, 0.0))
        new_value = _safe_float(event.new_value, previous)
        recent_changes.append(
            {
                "event_type": event.event_type,
                "reason": event.reason,
                "previous_score": round(previous, 4),
                "new_score": round(new_value, 4),
                "delta": round(new_value - previous, 4),
                "timestamp": _iso(event.timestamp),
            }
        )

    return {
        "user_id": user.id,
        "username": username,
        "trust_score": _safe_float(base_profile.get("trust_score"), 0.0),
        "trust_penalty": _safe_float(base_profile.get("trust_penalty"), 0.0),
        "trust_level": str(base_profile.get("trust_level") or "unknown"),
        "total_requests": _coerce_int(stats_row.total_requests),
        "blocked_requests": _coerce_int(stats_row.blocked_requests),
        "challenged_requests": _coerce_int(stats_row.challenged_requests),
        "last_activity": _iso(stats_row.last_activity),
        "recent_changes": recent_changes,
    }


@router.post("/zta/toggle")
async def toggle_zta(
    current_user: TokenData = Depends(require_admin),
):
    global _ZTA_LAST_UPDATED_AT
    settings = get_settings()
    current = settings.ZTA_ENABLED

    os.environ["ZTA_ENABLED"] = str(not current).upper()
    get_settings.cache_clear()
    _ZTA_LAST_UPDATED_AT = _utc_now()

    new_state = get_settings().ZTA_ENABLED
    response = _zta_payload(enabled=bool(new_state), previous_state=bool(current))
    response["message"] = f"ZTA {'enabled' if new_state else 'disabled'}"
    return response


@router.get("/zta/status")
async def zta_status(
    current_user: TokenData = Depends(require_active_user),
):
    return _zta_payload(enabled=bool(get_settings().ZTA_ENABLED))


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
        func.avg(RequestLog.prompt_risk_score).label("avg_prompt_risk_score"),
        func.avg(RequestLog.latency_ms).label("avg_latency_ms"),
    )

    result = await db.execute(query)
    row = result.one()

    total_requests = int(row.total_requests or 0)
    blocked_requests = int(row.blocked_requests or 0)
    challenged_requests = int(row.challenged_requests or 0)
    allowed_requests = int(row.allowed_requests or 0)
    avg_security_score = round(float(row.avg_security_score or 0.0), 4)
    avg_prompt_risk_score = round(float(row.avg_prompt_risk_score or 0.0), 4)
    avg_latency_ms = round(float(row.avg_latency_ms or 0.0), 2)
    block_rate = round((blocked_requests / total_requests) * 100, 2) if total_requests else 0.0

    model_counts = (
        await db.execute(
            select(
                func.count(Model.id).label("total_models"),
                func.sum(case((Model.is_active.is_(True), 1), else_=0)).label("active_models"),
            )
        )
    ).one()

    total_models = int(model_counts.total_models or 0)
    active_models = int(model_counts.active_models or 0)

    return {
        "total_requests": total_requests,
        "blocked_requests": blocked_requests,
        "challenged_requests": challenged_requests,
        "allowed_requests": allowed_requests,
        "avg_security_score": avg_security_score,
        "avg_prompt_risk_score": avg_prompt_risk_score,
        "avg_latency_ms": avg_latency_ms,
        "total_models": total_models,
        "active_models": active_models,
        "block_rate": block_rate,
    }


@router.get("/research/summary")
async def my_research_summary(
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(require_active_user),
):
    return await get_user_attack_sequence_summary(db, user_id=current_user.user_id)


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
    user_ids = [row.user_id for row in rows if row.user_id is not None]
    model_ids = [row.model_id for row in rows if row.model_id is not None]

    usernames_by_id: dict[int, str] = {}
    if user_ids:
        user_rows = (
            await db.execute(select(User.id, User.username).where(User.id.in_(set(user_ids))))
        ).all()
        usernames_by_id = {int(uid): str(uname) for uid, uname in user_rows}

    model_names_by_id: dict[int, str] = {}
    if model_ids:
        model_rows = (
            await db.execute(select(Model.id, Model.name).where(Model.id.in_(set(model_ids))))
        ).all()
        model_names_by_id = {int(mid): str(mname) for mid, mname in model_rows}

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
            "decision_reason": row.reason,
            "username": usernames_by_id.get(int(row.user_id)) if row.user_id is not None else None,
            "model_name": model_names_by_id.get(int(row.model_id)) if row.model_id is not None else None,
            "decision_input_snapshot": row.decision_input_snapshot,
            "decision_trace": row.decision_trace,
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
    model_ids = [row.model_id for row in rows if row.model_id is not None]

    model_names_by_id: dict[int, str] = {}
    if model_ids:
        model_rows = (
            await db.execute(select(Model.id, Model.name).where(Model.id.in_(set(model_ids))))
        ).all()
        model_names_by_id = {int(mid): str(mname) for mid, mname in model_rows}

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
            "decision_reason": row.reason,
            "username": current_user.username,
            "model_name": model_names_by_id.get(int(row.model_id)) if row.model_id is not None else None,
            "decision_input_snapshot": row.decision_input_snapshot,
            "decision_trace": row.decision_trace,
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
    db: AsyncSession = Depends(get_db),
):
    if current_user.username != username and "admin" not in current_user.scopes:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view your own trust profile",
        )
    base_profile = await get_trust_profile_persistent(db, username)
    return await _build_enriched_trust_profile(
        db,
        username=username,
        base_profile=base_profile,
        recent_limit=10,
    )


@router.get("/users/trust/all")
async def all_trust_profiles(
    current_user: TokenData = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    base_profiles = await list_trust_profiles_persistent(db)
    enriched = []
    for profile in base_profiles:
        username = str(profile.get("username") or "")
        if not username:
            continue
        enriched.append(
            await _build_enriched_trust_profile(
                db,
                username=username,
                base_profile=profile,
                recent_limit=3,
            )
        )
    return enriched


@router.post("/users/{username}/trust/reset")
async def reset_user_trust(
    username: str,
    current_user: TokenData = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    new_score = await reset_user_trust_persistent(
        db,
        username=username,
        reason=f"Trust score reset by admin {current_user.username}.",
    )
    base_profile = await get_trust_profile_persistent(db, username)
    profile = await _build_enriched_trust_profile(
        db,
        username=username,
        base_profile=base_profile,
        recent_limit=5,
    )
    return {
        "message": f"Trust score reset for {username}",
        "new_score": new_score,
        "profile": profile,
    }


@router.get("/users/{username}/trust/events")
async def user_trust_events(
    username: str,
    limit: int = Query(default=50, ge=1, le=500),
    current_user: TokenData = Depends(require_active_user),
    db: AsyncSession = Depends(get_db),
):
    if current_user.username != username and "admin" not in current_user.scopes:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view your own trust events",
        )

    user = (await db.execute(select(User).where(User.username == username))).scalar_one_or_none()
    if user is None:
        return {"username": username, "total": 0, "events": []}

    rows = (
        await db.execute(
            select(UserTrustEvent)
            .where(UserTrustEvent.user_id == user.id)
            .order_by(UserTrustEvent.timestamp.desc())
            .limit(limit)
        )
    ).scalars().all()

    return {
        "username": username,
        "total": len(rows),
        "events": [
            {
                "id": row.id,
                "event_type": row.event_type,
                "previous_value": row.previous_value,
                "new_value": row.new_value,
                "reason": row.reason,
                "context_json": row.context_json or {},
                "timestamp": row.timestamp.isoformat() if row.timestamp else None,
            }
            for row in rows
        ],
    }


@router.get("/models/{model_id}/posture/events")
async def model_posture_events(
    model_id: int,
    limit: int = Query(default=50, ge=1, le=500),
    current_user: TokenData = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    rows = (
        await db.execute(
            select(ModelPostureEvent)
            .where(ModelPostureEvent.model_id == model_id)
            .order_by(ModelPostureEvent.timestamp.desc())
            .limit(limit)
        )
    ).scalars().all()

    return {
        "model_id": model_id,
        "total": len(rows),
        "events": [
            {
                "id": row.id,
                "event_type": row.event_type,
                "metric_name": row.metric_name,
                "previous_value": row.previous_value,
                "new_value": row.new_value,
                "reason": row.reason,
                "context_json": row.context_json or {},
                "timestamp": row.timestamp.isoformat() if row.timestamp else None,
            }
            for row in rows
        ],
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
    return _normalize_rate_profile(get_rate_profile(username))


@router.get("/users/rate/all")
async def all_rate_profiles(
    current_user: TokenData = Depends(require_admin),
):
    return [_normalize_rate_profile(profile) for profile in get_all_rate_profiles()]


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
        func.avg(RequestLog.prompt_risk_score).label("avg_prompt_risk_score"),
        func.avg(RequestLog.latency_ms).label("avg_latency_ms"),
    )

    result = await db.execute(query)
    row = result.one()

    total_requests = int(row.total_requests or 0)
    blocked_requests = int(row.blocked_requests or 0)
    challenged_requests = int(row.challenged_requests or 0)
    allowed_requests = int(row.allowed_requests or 0)
    avg_security_score = round(float(row.avg_security_score or 0.0), 4)
    avg_prompt_risk_score = round(float(row.avg_prompt_risk_score or 0.0), 4)
    avg_latency_ms = round(float(row.avg_latency_ms or 0.0), 2)
    block_rate = round((blocked_requests / total_requests) * 100, 2) if total_requests else 0.0

    rate_profiles = get_all_rate_profiles()
    active_users = [r for r in rate_profiles if r["requests_in_window"] > 0]
    flagged_users = [r for r in active_users if r["is_rate_limited"]]
    now = _utc_now()
    uptime_seconds = max(0, int((now - _MONITORING_STARTED_AT).total_seconds()))

    status_value = "healthy"
    if flagged_users or block_rate > 60 or avg_security_score > 0.8:
        status_value = "degraded"
    if block_rate > 85:
        status_value = "unhealthy"

    return {
        "status": status_value,
        "database": "up",
        "cache": "up",
        "models_service": "up",
        "detection_service": "up",
        "uptime_seconds": uptime_seconds,
        "last_check": _iso(now),
        "metrics": {
            "total_requests": total_requests,
            "blocked_requests": blocked_requests,
            "challenged_requests": challenged_requests,
            "allowed_requests": allowed_requests,
            "avg_security_score": avg_security_score,
            "avg_prompt_risk_score": avg_prompt_risk_score,
            "avg_latency_ms": avg_latency_ms,
            "block_rate": block_rate,
        },
        "active_users": len(active_users),
        "flagged_users": flagged_users,
    }
