import time
from collections import defaultdict, deque

from app.schemas import RequestDecision

# username -> trust score (0.0 to 1.0, higher is better)
_user_trust_scores: dict[str, float] = defaultdict(lambda: 0.8)

# Keep a bounded window of recent behavior to support secure-mode adaptation.
_BEHAVIOR_WINDOW_SECONDS = 30 * 60
_BEHAVIOR_EVENT_LIMIT = 120
_user_behavior_events: dict[str, deque[dict]] = defaultdict(
    lambda: deque(maxlen=_BEHAVIOR_EVENT_LIMIT)
)


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, value))


def _now() -> float:
    return time.time()


def _normalize_decision_value(decision: RequestDecision | str) -> str:
    if hasattr(decision, "value"):
        return str(decision.value)
    return str(decision)


def _prune_behavior_events(username: str) -> None:
    cutoff = _now() - _BEHAVIOR_WINDOW_SECONDS
    events = _user_behavior_events[username]
    while events and float(events[0].get("timestamp", 0.0)) < cutoff:
        events.popleft()


def _coerce_float(value, default: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:
        return float(default)


def get_trust_score(username: str) -> float:
    return float(_user_trust_scores[username])


def get_user_trust_penalty(username: str) -> float:
    """
    Converts trust score to penalty for policy engine.
    Higher penalty = less trusted user.
    """
    score = get_trust_score(username)

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


def update_trust_score(username: str, decision: RequestDecision | str) -> float:
    """
    Adjust trust score after each request outcome.
    - allow: slight recovery
    - challenge: slight decrease
    - block: stronger decrease
    """
    current = get_trust_score(username)

    decision_value = _normalize_decision_value(decision)

    if decision_value == "allow":
        current += 0.01
    elif decision_value == "challenge":
        current -= 0.04
    elif decision_value == "block":
        current -= 0.08

    current = _clamp(current)
    _user_trust_scores[username] = current
    return current


def record_behavior_event(
    username: str,
    decision: RequestDecision | str,
    *,
    prompt_risk_score: float | None = None,
    security_score: float | None = None,
    request_rate_score: float | None = None,
    secure_mode_enabled: bool = False,
) -> dict:
    """
    Records recent behavior context for adaptive secure-mode enforcement.
    This is intentionally in-memory and bounded for predictable runtime behavior.
    """
    decision_value = _normalize_decision_value(decision).lower()
    prompt_risk = _coerce_float(prompt_risk_score, 0.0)
    security = _coerce_float(security_score, 0.0)
    rate_score = _coerce_float(request_rate_score, 0.0)

    risky_event = (
        decision_value in {"challenge", "block"}
        or prompt_risk >= 0.55
        or security >= 0.65
        or rate_score >= 0.65
    )

    entry = {
        "timestamp": _now(),
        "decision": decision_value,
        "risky_event": risky_event,
        "prompt_risk_score": round(prompt_risk, 4),
        "security_score": round(security, 4),
        "request_rate_score": round(rate_score, 4),
        "secure_mode_enabled": bool(secure_mode_enabled),
    }

    _prune_behavior_events(username)
    _user_behavior_events[username].append(entry)

    return get_behavior_context(username)


def get_behavior_context(username: str) -> dict:
    _prune_behavior_events(username)
    events = list(_user_behavior_events[username])

    recent_risky_events = sum(1 for event in events if event.get("risky_event"))
    recent_blocks = sum(1 for event in events if event.get("decision") == "block")
    recent_challenges = sum(1 for event in events if event.get("decision") == "challenge")
    recent_allows = sum(1 for event in events if event.get("decision") == "allow")
    high_risk_events = sum(
        1
        for event in events
        if float(event.get("prompt_risk_score") or 0.0) >= 0.75
        or float(event.get("security_score") or 0.0) >= 0.75
    )
    high_rate_events = sum(1 for event in events if float(event.get("request_rate_score") or 0.0) >= 0.65)

    anomaly_flags = []
    if len(events) >= 20:
        anomaly_flags.append("request_volume_spike")
    if recent_blocks >= 3:
        anomaly_flags.append("repeated_blocks")
    if recent_challenges >= 5:
        anomaly_flags.append("repeated_challenges")
    if high_risk_events >= 4:
        anomaly_flags.append("high_risk_cluster")
    if high_rate_events >= 3:
        anomaly_flags.append("rate_pressure")

    last_event = events[-1] if events else None

    return {
        "window_seconds": _BEHAVIOR_WINDOW_SECONDS,
        "events_considered": len(events),
        "recent_risky_events": recent_risky_events,
        "recent_blocks": recent_blocks,
        "recent_challenges": recent_challenges,
        "recent_allows": recent_allows,
        "high_risk_events": high_risk_events,
        "high_rate_events": high_rate_events,
        "anomaly_flags": anomaly_flags,
        "last_decision": (last_event or {}).get("decision"),
        "last_event_at": (last_event or {}).get("timestamp"),
    }


def reset_trust_score(username: str) -> float:
    _user_trust_scores[username] = 0.8
    _user_behavior_events[username].clear()
    return _user_trust_scores[username]


def set_trust_score(username: str, score: float) -> float:
    _user_trust_scores[username] = _clamp(score)
    return _user_trust_scores[username]


def get_trust_profile(username: str) -> dict:
    score = get_trust_score(username)
    penalty = get_user_trust_penalty(username)

    if score >= 0.9:
        level = "high"
    elif score >= 0.7:
        level = "good"
    elif score >= 0.5:
        level = "moderate"
    elif score >= 0.3:
        level = "low"
    else:
        level = "critical"

    return {
        "username": username,
        "trust_score": round(score, 4),
        "trust_penalty": round(penalty, 4),
        "trust_level": level,
    }


def get_all_trust_profiles() -> list[dict]:
    profiles = [get_trust_profile(username) for username in _user_trust_scores.keys()]
    profiles.sort(key=lambda x: x["trust_score"])
    return profiles
