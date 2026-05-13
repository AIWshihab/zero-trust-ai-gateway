import time
from collections import defaultdict

from app.core.config import get_settings

settings = get_settings()

# username -> list of request timestamps
_request_history: dict[str, list[float]] = defaultdict(list)
_abuse_profiles: dict[str, dict[str, float | int | str | None]] = defaultdict(
    lambda: {
        "strikes": 0,
        "cooldown_until": 0.0,
        "last_violation_at": 0.0,
        "last_reason": None,
    }
)

_ABUSE_STRIKE_WINDOW_SECONDS = 15 * 60
_ABUSE_DECAY_SECONDS = 30 * 60
_BASE_COOLDOWN_SECONDS = 5 * 60
_MAX_COOLDOWN_SECONDS = 60 * 60


def _now() -> float:
    return time.time()


def _remaining_seconds(timestamp: float) -> int:
    return max(0, int(round(timestamp - _now())))


def _prune(username: str) -> None:
    current = _now()
    window_start = current - settings.RATE_LIMIT_WINDOW_SECONDS
    _request_history[username] = [
        ts for ts in _request_history[username]
        if ts >= window_start
    ]


def record_request(username: str) -> None:
    _prune(username)
    _request_history[username].append(_now())


def is_rate_limited(username: str) -> bool:
    _prune(username)
    return len(_request_history[username]) >= settings.RATE_LIMIT_REQUESTS


def get_penalty_profile(username: str) -> dict:
    profile = _abuse_profiles[username]
    now = _now()

    last_violation_at = float(profile.get("last_violation_at") or 0.0)
    if last_violation_at and now - last_violation_at > _ABUSE_DECAY_SECONDS:
        profile["strikes"] = max(0, int(profile.get("strikes") or 0) - 1)
        profile["last_violation_at"] = now

    cooldown_until = float(profile.get("cooldown_until") or 0.0)
    return {
        "strikes": int(profile.get("strikes") or 0),
        "penalty_active": cooldown_until > now,
        "cooldown_until": cooldown_until if cooldown_until > now else None,
        "cooldown_remaining_seconds": _remaining_seconds(cooldown_until),
        "last_violation_at": last_violation_at or None,
        "last_reason": profile.get("last_reason"),
    }


def is_penalty_active(username: str) -> bool:
    return bool(get_penalty_profile(username)["penalty_active"])


def record_abuse_outcome(
    username: str,
    *,
    decision: str,
    prompt_risk_score: float = 0.0,
    security_score: float = 0.0,
    reason: str | None = None,
) -> dict:
    decision_value = str(decision).lower()
    high_risk = max(float(prompt_risk_score or 0.0), float(security_score or 0.0))

    if decision_value not in {"block", "challenge"} and high_risk < 0.55:
        return get_penalty_profile(username)

    profile = _abuse_profiles[username]
    now = _now()
    last_violation_at = float(profile.get("last_violation_at") or 0.0)

    if not last_violation_at or now - last_violation_at > _ABUSE_STRIKE_WINDOW_SECONDS:
        profile["strikes"] = 0

    severity = 1
    if decision_value == "block" or high_risk >= 0.75:
        severity = 2
    if high_risk >= 0.90:
        severity = 3

    strikes = min(12, int(profile.get("strikes") or 0) + severity)
    profile["strikes"] = strikes
    profile["last_violation_at"] = now
    profile["last_reason"] = reason or "Risky prompt or policy violation"

    if strikes >= 4:
        cooldown_seconds = min(_MAX_COOLDOWN_SECONDS, _BASE_COOLDOWN_SECONDS * (2 ** min(5, strikes - 4)))
        profile["cooldown_until"] = max(float(profile.get("cooldown_until") or 0.0), now + cooldown_seconds)

    return get_penalty_profile(username)


def get_request_rate_score(username: str) -> float:
    """
    Returns 0.0 to 1.0 risk score based on how close the user is
    to the configured request limit within the current time window.
    """
    _prune(username)

    count = len(_request_history[username])
    limit = max(settings.RATE_LIMIT_REQUESTS, 1)

    ratio = count / limit

    if ratio <= 0.25:
        return 0.05
    if ratio <= 0.50:
        return 0.15
    if ratio <= 0.75:
        return 0.35
    if ratio < 1.0:
        return 0.65
    return 1.0


def get_rate_profile(username: str) -> dict:
    _prune(username)

    count = len(_request_history[username])
    limit = settings.RATE_LIMIT_REQUESTS
    score = get_request_rate_score(username)
    penalty = get_penalty_profile(username)

    return {
        "username": username,
        "requests_in_window": count,
        "window_seconds": settings.RATE_LIMIT_WINDOW_SECONDS,
        "limit": limit,
        "rate_score": score,
        "is_rate_limited": count >= limit,
        "abuse_strikes": penalty["strikes"],
        "penalty_active": penalty["penalty_active"],
        "cooldown_remaining_seconds": penalty["cooldown_remaining_seconds"],
        "last_penalty_reason": penalty["last_reason"],
    }


def get_all_rate_profiles() -> list[dict]:
    profiles = []

    for username in list(_request_history.keys()):
        _prune(username)
        profiles.append(get_rate_profile(username))

    profiles.sort(key=lambda x: x["requests_in_window"], reverse=True)
    return profiles


def reset_rate_profile(username: str) -> dict:
    _request_history[username] = []
    _abuse_profiles[username] = {
        "strikes": 0,
        "cooldown_until": 0.0,
        "last_violation_at": 0.0,
        "last_reason": None,
    }
    return get_rate_profile(username)


def reset_all_rate_profiles() -> dict:
    for username in list(_request_history.keys()):
        _request_history[username] = []
    for username in list(_abuse_profiles.keys()):
        reset_rate_profile(username)

    return {
        "message": "All rate profiles reset",
        "total_users": len(_request_history),
    }
