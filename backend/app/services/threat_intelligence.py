from __future__ import annotations

from collections import Counter
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.attack_sequence_event import AttackSequenceEvent
from app.models.model import Model
from app.models.request_log import RequestLog
from app.models.user_trust_event import UserTrustEvent

ATTACK_WINDOW_MINUTES = 30
RESEARCH_METRIC_LIMIT = 5000

RISKY_STAGES = {
    "suspicious_probing",
    "prompt_injection",
    "secret_extraction_attempt",
    "jailbreak_attempt",
    "repeated_blocked_attempt",
    "cooldown_triggered",
}

STAGE_BASE_SEVERITY = {
    "safe_prompt": 0.05,
    "suspicious_probing": 0.30,
    "prompt_injection": 0.55,
    "secret_extraction_attempt": 0.70,
    "jailbreak_attempt": 0.76,
    "repeated_blocked_attempt": 0.84,
    "cooldown_triggered": 0.95,
}


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _event_time(event: AttackSequenceEvent) -> datetime:
    value = event.timestamp or _utc_now()
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


def _normalize_decision(decision: Any) -> str:
    if hasattr(decision, "value"):
        return str(decision.value).lower()
    return str(decision or "allow").lower()


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:
        return float(default)


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def _flag_text(flags: list[str] | None, reason: str | None = None) -> str:
    joined = " ".join(flags or [])
    if reason:
        joined = f"{joined} {reason}"
    return joined.lower()


def classify_attack_stage(
    *,
    flags: list[str] | None = None,
    decision: Any = "allow",
    risk_score: float | None = None,
    security_score: float | None = None,
    cooldown_active: bool = False,
    repeated_pattern_count: int = 0,
    reason: str | None = None,
) -> str:
    decision_value = _normalize_decision(decision)
    risk = _clamp(_safe_float(risk_score, 0.0))
    security = _clamp(_safe_float(security_score, 0.0))
    text = _flag_text(flags, reason)

    if cooldown_active:
        return "cooldown_triggered"
    if repeated_pattern_count >= 3 and decision_value == "block":
        return "repeated_blocked_attempt"
    if "jailbreak" in text or "dan" in text or "bypass_safety" in text or "disable_safety" in text:
        return "jailbreak_attempt"
    if "extraction" in text or "secret" in text or "credential" in text or "api_key" in text or "private_key" in text:
        return "secret_extraction_attempt"
    if "injection" in text or "ignore_instructions" in text or "system_prompt" in text:
        return "prompt_injection"
    if decision_value in {"challenge", "block"} or risk >= 0.35 or security >= 0.50:
        return "suspicious_probing"
    return "safe_prompt"


def _sequence_severity(stage: str, risk_score: float, security_score: float) -> float:
    return round(_clamp(max(STAGE_BASE_SEVERITY.get(stage, 0.1), risk_score, security_score)), 4)


def _is_risky_event(event: AttackSequenceEvent) -> bool:
    return (
        event.attack_stage in RISKY_STAGES
        or str(event.decision).lower() in {"challenge", "block"}
        or _safe_float(event.sequence_severity) >= 0.35
    )


def _summary_from_events(events: list[AttackSequenceEvent]) -> dict[str, Any]:
    if not events:
        return {
            "window_minutes": ATTACK_WINDOW_MINUTES,
            "recent_attack_stages": [],
            "sequence_severity": 0.0,
            "repeated_pattern_count": 0,
            "last_attack_type": None,
            "escalation_reason": None,
            "cross_model_abuse_score": 0.0,
            "cross_model_models": 0,
            "cross_model_risky_events": 0,
            "event_count": 0,
        }

    newest_first = sorted(events, key=_event_time, reverse=True)
    risky = [event for event in newest_first if _is_risky_event(event)]
    stage_counts = Counter(event.attack_stage for event in risky if event.attack_stage != "safe_prompt")
    model_ids = {event.model_id for event in risky if event.model_id is not None}
    repeated_count = max(stage_counts.values(), default=0)

    cross_model_score = 0.0
    if len(model_ids) >= 2 and len(risky) >= 3:
        cross_model_score = min(1.0, 0.25 * len(model_ids) + 0.08 * len(risky))

    sequence_severity = max((_safe_float(event.sequence_severity) for event in newest_first), default=0.0)
    last_attack = next((event for event in newest_first if event.attack_stage != "safe_prompt"), None)

    reasons = []
    if sequence_severity >= 0.75:
        reasons.append("high sequence severity")
    if repeated_count >= 3:
        reasons.append("repeated risky pattern")
    if cross_model_score >= 0.55:
        reasons.append("cross-model abuse pattern detected")

    return {
        "window_minutes": ATTACK_WINDOW_MINUTES,
        "recent_attack_stages": [event.attack_stage for event in newest_first[:10]],
        "sequence_severity": round(sequence_severity, 4),
        "repeated_pattern_count": int(repeated_count),
        "last_attack_type": last_attack.attack_stage if last_attack else None,
        "escalation_reason": "; ".join(reasons) if reasons else None,
        "cross_model_abuse_score": round(cross_model_score, 4),
        "cross_model_models": len(model_ids),
        "cross_model_risky_events": len(risky),
        "event_count": len(newest_first),
    }


async def get_user_attack_sequence_summary(
    db: AsyncSession,
    *,
    user_id: int | None,
    window_minutes: int = ATTACK_WINDOW_MINUTES,
) -> dict[str, Any]:
    if user_id is None:
        return _summary_from_events([])

    cutoff = _utc_now() - timedelta(minutes=window_minutes)
    rows = (
        await db.execute(
            select(AttackSequenceEvent)
            .where(AttackSequenceEvent.user_id == user_id, AttackSequenceEvent.timestamp >= cutoff)
            .order_by(AttackSequenceEvent.timestamp.desc())
            .limit(250)
        )
    ).scalars().all()

    summary = _summary_from_events(list(rows))
    summary["window_minutes"] = window_minutes
    return summary


async def update_attack_sequence(
    db: AsyncSession,
    *,
    user_id: int | None,
    model_id: int | None,
    event_type: str,
    decision: Any,
    risk_score: float | None = None,
    security_score: float | None = None,
    reason: str | None = None,
    flags: list[str] | None = None,
    prompt_hash: str | None = None,
    cooldown_active: bool = False,
    metadata: dict[str, Any] | None = None,
    commit: bool = False,
) -> AttackSequenceEvent | None:
    if user_id is None:
        return None

    cutoff = _utc_now() - timedelta(minutes=ATTACK_WINDOW_MINUTES)
    recent = (
        await db.execute(
            select(AttackSequenceEvent)
            .where(AttackSequenceEvent.user_id == user_id, AttackSequenceEvent.timestamp >= cutoff)
            .order_by(AttackSequenceEvent.timestamp.desc())
            .limit(250)
        )
    ).scalars().all()

    risk = _clamp(_safe_float(risk_score, 0.0))
    security = _clamp(_safe_float(security_score, 0.0))

    provisional_stage = classify_attack_stage(
        flags=flags,
        decision=decision,
        risk_score=risk,
        security_score=security,
        cooldown_active=cooldown_active,
        repeated_pattern_count=0,
        reason=reason,
    )
    repeated_count = 1 + sum(1 for event in recent if event.attack_stage == provisional_stage and event.attack_stage != "safe_prompt")
    stage = classify_attack_stage(
        flags=flags,
        decision=decision,
        risk_score=risk,
        security_score=security,
        cooldown_active=cooldown_active,
        repeated_pattern_count=repeated_count,
        reason=reason,
    )
    if stage != provisional_stage and stage != "safe_prompt":
        repeated_count = 1 + sum(1 for event in recent if event.attack_stage == stage)

    synthetic_events = list(recent)
    row = AttackSequenceEvent(
        user_id=user_id,
        model_id=model_id,
        event_type=event_type,
        attack_stage=stage,
        decision=_normalize_decision(decision),
        risk_score=round(risk, 4),
        security_score=round(security, 4),
        sequence_severity=_sequence_severity(stage, risk, security),
        repeated_pattern_count=int(repeated_count),
        cross_model_score=0.0,
        reason=reason,
        metadata_json={
            "prompt_hash": prompt_hash,
            "flags": list(flags or []),
            **(metadata or {}),
        },
    )
    synthetic_events.append(row)
    row.cross_model_score = _summary_from_events(synthetic_events)["cross_model_abuse_score"]

    db.add(row)
    await db.flush()
    if commit:
        await db.commit()
        await db.refresh(row)
    return row


async def build_research_metrics(db: AsyncSession) -> dict[str, Any]:
    events = (
        await db.execute(
            select(AttackSequenceEvent)
            .order_by(AttackSequenceEvent.timestamp.desc())
            .limit(RESEARCH_METRIC_LIMIT)
        )
    ).scalars().all()

    stage_counts = Counter(event.attack_stage for event in events)
    total_sequences = len(events)
    avg_severity = (
        sum(_safe_float(event.sequence_severity) for event in events) / total_sequences
        if total_sequences
        else 0.0
    )

    logs = (
        await db.execute(
            select(RequestLog)
            .order_by(RequestLog.timestamp.desc())
            .limit(RESEARCH_METRIC_LIMIT)
        )
    ).scalars().all()

    adaptive_activations = 0
    cross_model_reasons = 0
    review_candidates = []
    for log in logs:
        trace = log.decision_trace or {}
        reasons = trace.get("adaptive_reasons") or []
        if reasons:
            adaptive_activations += 1
        if any("cross-model" in str(reason).lower() for reason in reasons):
            cross_model_reasons += 1
        if (
            str(log.decision).lower() in {"challenge", "block"}
            and _safe_float(log.prompt_risk_score) < 0.35
            and _safe_float(log.security_score) < 0.50
        ):
            review_candidates.append(
                {
                    "log_id": log.id,
                    "model_id": log.model_id,
                    "decision": log.decision,
                    "prompt_risk_score": log.prompt_risk_score,
                    "security_score": log.security_score,
                    "reason": log.reason,
                }
            )

    trust_drop_rows = (
        await db.execute(
            select(func.count(UserTrustEvent.id)).where(
                UserTrustEvent.new_value < UserTrustEvent.previous_value,
                UserTrustEvent.reason.ilike("%abuse%"),
            )
        )
    ).scalar_one()

    model_row = (
        await db.execute(
            select(
                func.avg(Model.base_risk_score).label("avg_base_risk"),
                func.avg(Model.secured_risk_score).label("avg_secured_risk"),
                func.avg(case((Model.secure_mode_enabled.is_(True), Model.risk_reduction_pct), else_=None)).label("secure_mode_reduction"),
            )
        )
    ).one()

    cooldown_triggers = stage_counts.get("cooldown_triggered", 0)
    cross_model_detections = sum(1 for event in events if _safe_float(event.cross_model_score) >= 0.55)

    return {
        "attack_sequence_count": total_sequences,
        "top_attack_categories": [
            {"attack_stage": stage, "count": count}
            for stage, count in stage_counts.most_common(10)
        ],
        "average_sequence_severity": round(avg_severity, 4),
        "adaptive_threshold_activations": adaptive_activations,
        "cross_model_abuse_detections": max(cross_model_detections, cross_model_reasons),
        "cooldown_triggers": cooldown_triggers,
        "trust_drops_caused_by_repeated_abuse": int(trust_drop_rows or 0),
        "base_risk_vs_secured_risk": {
            "avg_base_risk_score": round(_safe_float(model_row.avg_base_risk), 2),
            "avg_secured_risk_score": round(_safe_float(model_row.avg_secured_risk), 2),
            "avg_risk_delta": round(_safe_float(model_row.avg_base_risk) - _safe_float(model_row.avg_secured_risk), 2),
        },
        "risk_reduction_under_secure_mode": round(_safe_float(model_row.secure_mode_reduction), 2),
        "false_positive_review_helpers": {
            "candidate_count": len(review_candidates),
            "candidates": review_candidates[:25],
        },
    }
