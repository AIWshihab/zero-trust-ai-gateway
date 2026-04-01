import time
from collections import defaultdict

from app.core.config import get_settings

settings = get_settings()

# username -> list of request timestamps
_request_history: dict[str, list[float]] = defaultdict(list)


def _now() -> float:
    return time.time()


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

    return {
        "username": username,
        "requests_in_window": count,
        "window_seconds": settings.RATE_LIMIT_WINDOW_SECONDS,
        "limit": limit,
        "rate_score": score,
        "is_rate_limited": count >= limit,
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
    return get_rate_profile(username)


def reset_all_rate_profiles() -> dict:
    for username in list(_request_history.keys()):
        _request_history[username] = []

    return {
        "message": "All rate profiles reset",
        "total_users": len(_request_history),
    }