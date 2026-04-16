import json
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.trust_score import get_trust_profile, set_trust_score
from app.models.model import Model
from app.models.model_posture_event import ModelPostureEvent
from app.models.request_log import RequestLog
from app.models.user import User
from app.models.user_trust_event import UserTrustEvent
from app.schemas import RequestDecision
from app.services.model_posture_engine import build_control_context, compute_secured_risk_from_controls

TRUST_DEFAULT_SCORE = 0.8
TRUST_MIN_SCORE = 0.0
TRUST_MAX_SCORE = 1.0
REQUEST_COUNTER_LOOKBACK_MINUTES = 60


def _decision_value(decision: RequestDecision | str) -> str:
    if hasattr(decision, "value"):
        return str(decision.value).lower()
    return str(decision).lower()


def _clamp_score(value: float) -> float:
    return max(TRUST_MIN_SCORE, min(TRUST_MAX_SCORE, float(value)))


def _clamp_100(value: float) -> float:
    return max(0.0, min(100.0, float(value)))


def _safe_float(value: Any, default: float | None = None) -> float | None:
    if value is None:
        return default
    try:
        return float(value)
    except Exception:
        return default


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _normalize_datetime(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


def _trust_penalty_from_score(score: float) -> float:
    score = _clamp_score(score)
    if score >= 0.9:
        return 0.0
    if score >= 0.75:
        return 0.1
    if score >= 0.6:
        return 0.2
    if score >= 0.45:
        return 0.35
    if score >= 0.3:
        return 0.55
    return 0.8


def _trust_level_from_score(score: float) -> str:
    score = _clamp_score(score)
    if score >= 0.9:
        return "high"
    if score >= 0.7:
        return "good"
    if score >= 0.5:
        return "moderate"
    if score >= 0.3:
        return "low"
    return "critical"


def _extract_protection_config(scan_summary_json: str | None) -> dict[str, Any]:
    if not scan_summary_json:
        return {}
    try:
        parsed = json.loads(scan_summary_json)
    except Exception:
        return {}

    if not isinstance(parsed, dict):
        return {}

    protection = parsed.get("protection")
    if not isinstance(protection, dict):
        return {}

    config = protection.get("config")
    if not isinstance(config, dict):
        return {}

    return config


async def _recent_request_counters(
    db: AsyncSession,
    *,
    user_id: int | None = None,
    model_id: int | None = None,
    lookback_minutes: int = REQUEST_COUNTER_LOOKBACK_MINUTES,
) -> dict[str, int]:
    since = _now_utc() - timedelta(minutes=max(1, int(lookback_minutes)))
    query = select(
        func.count(RequestLog.id).label("total"),
        func.sum(case((RequestLog.decision == "block", 1), else_=0)).label("blocks"),
        func.sum(case((RequestLog.decision == "challenge", 1), else_=0)).label("challenges"),
        func.sum(case((RequestLog.decision == "allow", 1), else_=0)).label("allows"),
        func.sum(case((RequestLog.security_score >= 0.65, 1), else_=0)).label("high_security"),
        func.sum(case((RequestLog.prompt_risk_score >= 0.55, 1), else_=0)).label("high_prompt_risk"),
    ).where(RequestLog.timestamp >= since)

    if user_id is not None:
        query = query.where(RequestLog.user_id == user_id)
    if model_id is not None:
        query = query.where(RequestLog.model_id == model_id)

    row = (await db.execute(query)).one()
    return {
        "total": int(row.total or 0),
        "blocks": int(row.blocks or 0),
        "challenges": int(row.challenges or 0),
        "allows": int(row.allows or 0),
        "high_security": int(row.high_security or 0),
        "high_prompt_risk": int(row.high_prompt_risk or 0),
    }


async def _resolve_user(
    db: AsyncSession,
    *,
    user_id: int | None,
    username: str,
) -> User | None:
    user: User | None = None
    if user_id is not None:
        user = (
            await db.execute(select(User).where(User.id == user_id))
        ).scalar_one_or_none()
    if user is None:
        user = (
            await db.execute(select(User).where(User.username == username))
        ).scalar_one_or_none()
    return user


async def get_user_trust_penalty_persistent(
    db: AsyncSession,
    *,
    user_id: int | None,
    username: str,
) -> float:
    user = await _resolve_user(db, user_id=user_id, username=username)
    if user is None:
        score = _clamp_score(TRUST_DEFAULT_SCORE)
        set_trust_score(username, score)
        return _trust_penalty_from_score(score)

    score = _clamp_score(_safe_float(user.trust_score, TRUST_DEFAULT_SCORE) or TRUST_DEFAULT_SCORE)
    if user.trust_score != score:
        user.trust_score = score
        await db.flush()
    set_trust_score(username, score)
    return _trust_penalty_from_score(score)


async def reassess_user_trust_on_request(
    db: AsyncSession,
    *,
    user_id: int | None,
    username: str,
    decision: RequestDecision | str,
    prompt_risk_score: float,
    security_score: float,
    request_rate_score: float,
    secure_mode_enabled: bool,
    behavior_context: dict[str, Any] | None = None,
    reason_prefix: str | None = None,
    commit: bool = False,
) -> dict[str, Any]:
    user = await _resolve_user(db, user_id=user_id, username=username)
    previous_score = _clamp_score(
        _safe_float(getattr(user, "trust_score", None), TRUST_DEFAULT_SCORE) or TRUST_DEFAULT_SCORE
    )

    outcome = _decision_value(decision)
    base_deltas = {
        "allow": 0.01,
        "challenge": -0.04,
        "block": -0.08,
    }
    base_delta = base_deltas.get(outcome, -0.02)

    if user is None and user_id is None:
        recent = {
            "total": 0,
            "blocks": 0,
            "challenges": 0,
            "allows": 0,
            "high_security": 0,
            "high_prompt_risk": 0,
        }
    else:
        recent = await _recent_request_counters(db, user_id=getattr(user, "id", user_id))
    context_delta = 0.0
    reasons: list[str] = [reason_prefix] if reason_prefix else []
    reasons.append(f"request outcome={outcome}")

    if prompt_risk_score >= 0.75:
        context_delta -= 0.03
        reasons.append("very high prompt risk decreased trust")
    elif prompt_risk_score >= 0.55:
        context_delta -= 0.02
        reasons.append("elevated prompt risk decreased trust")

    if security_score >= 0.8:
        context_delta -= 0.03
        reasons.append("high security score decreased trust")
    elif security_score >= 0.6:
        context_delta -= 0.02
        reasons.append("moderate security pressure decreased trust")

    if request_rate_score >= 0.65:
        context_delta -= 0.02
        reasons.append("rate pressure decreased trust")

    if recent["blocks"] >= 3:
        context_delta -= 0.03
        reasons.append("recent repeated blocks decreased trust")
    elif recent["challenges"] >= 5:
        context_delta -= 0.02
        reasons.append("recent repeated challenges decreased trust")

    if recent["high_prompt_risk"] >= 6 or recent["high_security"] >= 6:
        context_delta -= 0.02
        reasons.append("sustained high-risk request pattern decreased trust")

    local_risky = int((behavior_context or {}).get("recent_risky_events", 0))
    if secure_mode_enabled and local_risky >= 6:
        context_delta -= 0.02
        reasons.append("secure-mode local risky streak decreased trust")

    if (
        outcome == "allow"
        and prompt_risk_score < 0.2
        and security_score < 0.25
        and request_rate_score < 0.35
        and recent["blocks"] == 0
        and recent["challenges"] <= 1
    ):
        context_delta += 0.005
        reasons.append("consistent compliant usage slightly restored trust")

    net_delta = max(-0.18, min(0.03, base_delta + context_delta))
    new_score = _clamp_score(previous_score + net_delta)

    if user is not None:
        user.trust_score = new_score
    set_trust_score(username, new_score)

    if user is not None:
        reason_text = "; ".join([r for r in reasons if r]) or "Trust reassessed from request outcome."
        trust_event = UserTrustEvent(
            user_id=user.id,
            username_snapshot=username,
            event_type="request_outcome_reassessment",
            previous_value=round(previous_score, 4),
            new_value=round(new_score, 4),
            reason=reason_text,
            context_json={
                "decision": outcome,
                "base_delta": round(base_delta, 4),
                "context_delta": round(context_delta, 4),
                "net_delta": round(net_delta, 4),
                "prompt_risk_score": round(float(prompt_risk_score), 4),
                "security_score": round(float(security_score), 4),
                "request_rate_score": round(float(request_rate_score), 4),
                "secure_mode_enabled": bool(secure_mode_enabled),
                "recent_persistent_counters": recent,
                "recent_behavior_context": behavior_context or {},
            },
        )
        db.add(trust_event)

    if commit:
        await db.commit()
    else:
        await db.flush()

    return {
        "username": username,
        "previous_trust_score": round(previous_score, 4),
        "new_trust_score": round(new_score, 4),
        "trust_penalty": round(_trust_penalty_from_score(new_score), 4),
        "trust_level": _trust_level_from_score(new_score),
        "recent_counters": recent,
    }


async def reassess_model_posture(
    db: AsyncSession,
    *,
    model_row: Model,
    trigger: str,
    request_context: dict[str, Any] | None = None,
    commit: bool = False,
) -> dict[str, Any]:
    now = _now_utc()
    request_context = request_context or {}
    posture_factors = dict(model_row.posture_factors or {})

    current_base_risk = _safe_float(model_row.base_risk_score)
    if current_base_risk is None:
        base_trust = _safe_float(model_row.base_trust_score, 50.0) or 50.0
        current_base_risk = _clamp_100(100.0 - base_trust)

    baseline_base_risk = _safe_float(posture_factors.get("baseline_base_risk_score"), current_base_risk) or current_base_risk

    stale_penalty = 0.0
    reasons: list[str] = []

    valid_until = _normalize_datetime(model_row.scan_valid_until)
    posture_assessed_at = _normalize_datetime(model_row.posture_assessed_at)
    if valid_until is None:
        stale_penalty += 8.0
        reasons.append("missing scan validity window increased risk")
    elif now > valid_until:
        days_overdue = max(1, (now - valid_until).days)
        stale_penalty += min(24.0, 6.0 + (days_overdue * 2.0))
        reasons.append(f"stale scan ({days_overdue} day(s) overdue) increased risk")
    elif (valid_until - now).days <= 2:
        stale_penalty += 2.0
        reasons.append("scan validity near expiry triggered precautionary risk increase")

    if posture_assessed_at is not None:
        model_row.scan_freshness_days = max(0, (now - posture_assessed_at).days)
    elif model_row.scan_freshness_days is None:
        model_row.scan_freshness_days = 0

    recent = await _recent_request_counters(db, model_id=model_row.id)
    behavior_penalty = 0.0
    if recent["blocks"] >= 4:
        behavior_penalty += 4.0
        reasons.append("repeated blocked requests increased model exposure risk")
    if recent["high_security"] >= 8 or recent["high_prompt_risk"] >= 8:
        behavior_penalty += 3.0
        reasons.append("high-risk traffic concentration increased posture risk")

    request_rate_score = _safe_float(request_context.get("request_rate_score"), 0.0) or 0.0
    if request_rate_score >= 0.8:
        behavior_penalty += 2.0
        reasons.append("current burst/rate pressure increased posture risk")

    outcome = _decision_value(str(request_context.get("decision") or "allow"))
    if outcome == "block":
        behavior_penalty += 1.0
        reasons.append("blocked request outcome contributed to risk pressure")
    elif outcome == "challenge":
        behavior_penalty += 0.5
        reasons.append("challenge outcome contributed to mild risk pressure")

    total_penalty = min(30.0, stale_penalty + behavior_penalty)
    new_base_risk = _clamp_100(baseline_base_risk + total_penalty)

    secure_mode_context = posture_factors.get("secure_mode_context") if isinstance(posture_factors, dict) else None
    control_context = (
        secure_mode_context.get("control_context")
        if isinstance(secure_mode_context, dict) and isinstance(secure_mode_context.get("control_context"), dict)
        else None
    )

    if control_context is None:
        control_context = build_control_context(
            settings=get_settings(),
            secure_mode_enabled=bool(model_row.secure_mode_enabled),
            protection_config=_extract_protection_config(model_row.scan_summary_json),
        )

    secured = compute_secured_risk_from_controls(
        base_risk_score=new_base_risk,
        control_context=control_context,
    )
    new_secured_risk = _clamp_100(_safe_float(secured.get("secured_risk_score"), new_base_risk) or new_base_risk)
    new_reduction = _clamp_100(_safe_float(secured.get("risk_reduction_pct"), 0.0) or 0.0)

    previous_base = _clamp_100(current_base_risk)
    previous_secured = _clamp_100(_safe_float(model_row.secured_risk_score, previous_base) or previous_base)
    previous_reduction = _clamp_100(_safe_float(model_row.risk_reduction_pct, 0.0) or 0.0)

    changed_base = abs(previous_base - new_base_risk) >= 0.01
    changed_secured = abs(previous_secured - new_secured_risk) >= 0.01
    changed_reduction = abs(previous_reduction - new_reduction) >= 0.01
    reassessed = changed_base or changed_secured or changed_reduction or bool(reasons)

    if reassessed:
        model_row.base_risk_score = new_base_risk
        model_row.secured_risk_score = new_secured_risk
        model_row.risk_reduction_pct = new_reduction
        model_row.last_reassessed_at = now

        posture_factors["baseline_base_risk_score"] = round(baseline_base_risk, 2)
        posture_factors["secured_risk_controls"] = secured.get("secured_risk_controls") or posture_factors.get("secured_risk_controls", {})
        posture_factors["continuous_reassessment"] = {
            "trigger": trigger,
            "reassessed_at": now.isoformat(),
            "stale_penalty_points": round(stale_penalty, 2),
            "behavior_penalty_points": round(behavior_penalty, 2),
            "total_penalty_points": round(total_penalty, 2),
            "request_context": request_context,
            "recent_model_counters": recent,
            "reasons": reasons,
        }
        model_row.posture_factors = posture_factors

        explanation_line = (
            f"Continuous reassessment ({trigger}) adjusted base risk "
            f"{round(previous_base, 2)} -> {round(new_base_risk, 2)} "
            f"and secured risk {round(previous_secured, 2)} -> {round(new_secured_risk, 2)}."
        )
        merged_explanations = [str(line) for line in (model_row.posture_explanations or []) if isinstance(line, str)]
        merged_explanations.append(explanation_line)
        for reason in reasons:
            merged_explanations.append(f"Reassessment reason: {reason}.")
        model_row.posture_explanations = merged_explanations[-30:]

        reason_text = "; ".join(reasons) or "Continuous model posture reassessment executed."
        if changed_base:
            db.add(
                ModelPostureEvent(
                    model_id=model_row.id,
                    model_name_snapshot=model_row.name,
                    event_type=f"{trigger}_reassessment",
                    metric_name="base_risk_score",
                    previous_value=round(previous_base, 2),
                    new_value=round(new_base_risk, 2),
                    reason=reason_text,
                    context_json={
                        "stale_penalty_points": round(stale_penalty, 2),
                        "behavior_penalty_points": round(behavior_penalty, 2),
                        "total_penalty_points": round(total_penalty, 2),
                        "recent_model_counters": recent,
                        "request_context": request_context,
                    },
                )
            )
        if changed_secured:
            db.add(
                ModelPostureEvent(
                    model_id=model_row.id,
                    model_name_snapshot=model_row.name,
                    event_type=f"{trigger}_reassessment",
                    metric_name="secured_risk_score",
                    previous_value=round(previous_secured, 2),
                    new_value=round(new_secured_risk, 2),
                    reason=reason_text,
                    context_json={
                        "risk_reduction_pct_previous": round(previous_reduction, 2),
                        "risk_reduction_pct_new": round(new_reduction, 2),
                        "secured_risk_controls": secured.get("secured_risk_controls"),
                    },
                )
            )
        if reasons and not changed_base and not changed_secured:
            db.add(
                ModelPostureEvent(
                    model_id=model_row.id,
                    model_name_snapshot=model_row.name,
                    event_type=f"{trigger}_reassessment",
                    metric_name="staleness_posture_signal",
                    previous_value=None,
                    new_value=None,
                    reason=reason_text,
                    context_json={
                        "stale_penalty_points": round(stale_penalty, 2),
                        "behavior_penalty_points": round(behavior_penalty, 2),
                        "total_penalty_points": round(total_penalty, 2),
                        "recent_model_counters": recent,
                        "request_context": request_context,
                    },
                )
            )

    if commit:
        await db.commit()
    else:
        await db.flush()

    return {
        "reassessed": reassessed,
        "base_risk_score": round(new_base_risk, 2),
        "secured_risk_score": round(new_secured_risk, 2),
        "risk_reduction_pct": round(new_reduction, 2),
        "reasons": reasons,
    }


async def get_trust_profile_persistent(db: AsyncSession, username: str) -> dict[str, Any]:
    user = (
        await db.execute(select(User).where(User.username == username))
    ).scalar_one_or_none()
    if user is None:
        return get_trust_profile(username)

    score = _clamp_score(_safe_float(user.trust_score, TRUST_DEFAULT_SCORE) or TRUST_DEFAULT_SCORE)
    set_trust_score(username, score)
    return {
        "username": username,
        "trust_score": round(score, 4),
        "trust_penalty": round(_trust_penalty_from_score(score), 4),
        "trust_level": _trust_level_from_score(score),
    }


async def list_trust_profiles_persistent(db: AsyncSession) -> list[dict[str, Any]]:
    rows = (
        await db.execute(select(User).order_by(User.trust_score.asc(), User.username.asc()))
    ).scalars().all()

    profiles = []
    for user in rows:
        score = _clamp_score(_safe_float(user.trust_score, TRUST_DEFAULT_SCORE) or TRUST_DEFAULT_SCORE)
        set_trust_score(user.username, score)
        profiles.append(
            {
                "username": user.username,
                "trust_score": round(score, 4),
                "trust_penalty": round(_trust_penalty_from_score(score), 4),
                "trust_level": _trust_level_from_score(score),
            }
        )
    return profiles


async def reset_user_trust_persistent(
    db: AsyncSession,
    *,
    username: str,
    reason: str = "Trust score reset by admin action.",
    reset_score: float = TRUST_DEFAULT_SCORE,
) -> float:
    user = (
        await db.execute(select(User).where(User.username == username))
    ).scalar_one_or_none()
    if user is None:
        set_trust_score(username, reset_score)
        return _clamp_score(reset_score)

    previous = _clamp_score(_safe_float(user.trust_score, TRUST_DEFAULT_SCORE) or TRUST_DEFAULT_SCORE)
    new_score = _clamp_score(reset_score)
    user.trust_score = new_score
    set_trust_score(username, new_score)

    db.add(
        UserTrustEvent(
            user_id=user.id,
            username_snapshot=username,
            event_type="manual_reset",
            previous_value=round(previous, 4),
            new_value=round(new_score, 4),
            reason=reason,
            context_json={"reset_score": round(new_score, 4)},
        )
    )
    await db.commit()
    return new_score
