from fastapi import APIRouter, Depends, Query
from app.core.security import require_active_user, require_admin
from app.models.schemas import TokenData, RequestDecision
from app.services.logger import (
    get_all_logs,
    get_logs_by_user,
    get_logs_by_decision,
    get_logs_by_model,
    get_metrics_summary,
)
from app.core.trust_score import (
    get_trust_profile,
    get_all_trust_profiles,
    reset_trust_score,
)
from app.core.rate_limiter import (
    get_rate_profile,
    get_all_rate_profiles,
)

router = APIRouter()

from app.core.config import get_settings
import os

@router.post("/zta/toggle")
async def toggle_zta(
    current_user: TokenData = Depends(require_admin),
):
    """
    Toggles ZTA on or off at runtime.
    Admin only. Used for Experiment 4 evaluation.
    """
    settings = get_settings()
    current  = settings.ZTA_ENABLED

    # Update env var at runtime
    os.environ["ZTA_ENABLED"] = str(not current).upper()

    # Bust the lru_cache so new value is picked up
    get_settings.cache_clear()

    new_state = get_settings().ZTA_ENABLED
    return {
        "previous_state": current,
        "new_state":       new_state,
        "message":         f"ZTA {'enabled' if new_state else 'disabled'}",
    }


@router.get("/zta/status")
async def zta_status(
    current_user: TokenData = Depends(require_active_user),
):
    """Returns current ZTA enabled/disabled state."""
    return {
        "zta_enabled": get_settings().ZTA_ENABLED,
        "message": "ZTA is active" if get_settings().ZTA_ENABLED else "⚠️ ZTA is disabled — no security enforcement",
    }


# ─── Metrics Summary ──────────────────────────────────────────────────────────

@router.get("/metrics")
async def metrics_summary(
    current_user: TokenData = Depends(require_active_user),
):
    """
    Aggregated system metrics for the monitoring dashboard.
    Covers Experiment 2, 3 & 4 evaluation data.
    """
    return get_metrics_summary()


# ─── Request Logs ─────────────────────────────────────────────────────────────

@router.get("/logs")
async def all_logs(
    limit: int = Query(default=50, le=500),
    decision: RequestDecision = Query(default=None),
    model_id: int = Query(default=None),
    current_user: TokenData = Depends(require_admin),
):
    """
    Paginated request logs with optional filters.
    Admin only.
    """
    if decision:
        logs = get_logs_by_decision(decision)
    elif model_id:
        logs = get_logs_by_model(model_id)
    else:
        logs = get_all_logs()

    return {
        "total": len(logs),
        "limit": limit,
        "logs":  logs[:limit],
    }


@router.get("/logs/me")
async def my_logs(
    current_user: TokenData = Depends(require_active_user),
):
    """
    Returns logs for the currently authenticated user only.
    """
    logs = get_logs_by_user(current_user.username)
    return {
        "username": current_user.username,
        "total":    len(logs),
        "logs":     logs,
    }


# ─── Trust Profiles ───────────────────────────────────────────────────────────

@router.get("/users/{username}/trust")
async def user_trust_profile(
    username: str,
    current_user: TokenData = Depends(require_active_user),
):
    """
    Returns trust score and history for a specific user.
    Users can only view their own profile unless admin.
    """
    if current_user.username != username and "admin" not in current_user.scopes:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view your own trust profile",
        )
    return get_trust_profile(username)


@router.get("/users/trust/all")
async def all_trust_profiles(
    current_user: TokenData = Depends(require_admin),
):
    """All user trust profiles. Admin only."""
    return get_all_trust_profiles()


@router.post("/users/{username}/trust/reset")
async def reset_user_trust(
    username: str,
    current_user: TokenData = Depends(require_admin),
):
    """Resets a user's trust score to 1.0. Admin only."""
    new_score = reset_trust_score(username)
    return {
        "message":   f"Trust score reset for {username}",
        "new_score": new_score,
    }


# ─── Rate Profiles ────────────────────────────────────────────────────────────

@router.get("/users/{username}/rate")
async def user_rate_profile(
    username: str,
    current_user: TokenData = Depends(require_active_user),
):
    """
    Returns rate limiting profile for a specific user.
    Used to detect model extraction patterns (Experiment 2).
    """
    if current_user.username != username and "admin" not in current_user.scopes:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view your own rate profile",
        )
    return get_rate_profile(username)


@router.get("/users/rate/all")
async def all_rate_profiles(
    current_user: TokenData = Depends(require_admin),
):
    """All user rate profiles. Admin only."""
    return get_all_rate_profiles()


# ─── System Health Summary ────────────────────────────────────────────────────

@router.get("/health")
async def monitoring_health(
    current_user: TokenData = Depends(require_active_user),
):
    """
    Combined system snapshot — metrics + active users being tracked.
    """
    metrics      = get_metrics_summary()
    rate_profiles = get_all_rate_profiles()
    active_users = [r for r in rate_profiles if r["requests_in_window"] > 0]

    return {
        "metrics":      metrics,
        "active_users": len(active_users),
        "flagged_users": [
            r for r in active_users if r["is_rate_limited"]
        ],
    }
