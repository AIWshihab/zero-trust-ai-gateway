from datetime import datetime, timedelta
from collections import defaultdict
from app.core.config import get_settings

settings = get_settings()


# ─── In-Memory Request Window Store ──────────────────────────────────────────

# Structure: { username: [timestamp1, timestamp2, ...] }
_request_windows: dict[str, list[datetime]] = defaultdict(list)


# ─── Sliding Window Rate Tracker ─────────────────────────────────────────────

def _clean_window(username: str) -> list[datetime]:
    """
    Removes timestamps outside the current sliding window.
    Returns the cleaned list of recent timestamps.
    """
    now    = datetime.utcnow()
    cutoff = now - timedelta(seconds=settings.RATE_LIMIT_WINDOW_SECONDS)

    _request_windows[username] = [
        ts for ts in _request_windows[username] if ts > cutoff
    ]
    return _request_windows[username]


def record_request(username: str) -> int:
    """
    Records a new request timestamp for the user.
    Returns current request count within the window.
    """
    _clean_window(username)
    _request_windows[username].append(datetime.utcnow())
    return len(_request_windows[username])


def get_request_count(username: str) -> int:
    """
    Returns how many requests the user has made
    within the current sliding window.
    """
    return len(_clean_window(username))


# ─── Rate Score for Policy Engine ────────────────────────────────────────────

def get_request_rate_score(username: str) -> float:
    """
    Returns a normalised rate score [0.0 - 1.0].
    Consumed directly by policy_engine.py.

    score = current_requests / max_allowed_requests
    Score of 1.0 means the user has hit or exceeded the limit.
    """
    count     = get_request_count(username)
    max_reqs  = settings.RATE_LIMIT_REQUESTS
    score     = min(count / max_reqs, 1.0)
    return round(score, 4)


# ─── Hard Rate Limit Check ────────────────────────────────────────────────────

def is_rate_limited(username: str) -> bool:
    """
    Hard boolean check — True if user exceeded the limit.
    Used as a fast-path guard before full policy evaluation.
    """
    return get_request_count(username) >= settings.RATE_LIMIT_REQUESTS


# ─── Rate Profile (for monitoring) ───────────────────────────────────────────

def get_rate_profile(username: str) -> dict:
    """
    Returns full rate limiting profile for a user.
    Used by monitoring dashboard.
    """
    count    = get_request_count(username)
    max_reqs = settings.RATE_LIMIT_REQUESTS
    window   = settings.RATE_LIMIT_WINDOW_SECONDS

    return {
        "username":          username,
        "requests_in_window": count,
        "max_requests":       max_reqs,
        "window_seconds":     window,
        "rate_score":         get_request_rate_score(username),
        "is_rate_limited":    is_rate_limited(username),
        "utilisation_pct":    round((count / max_reqs) * 100, 2),
    }


# ─── Reset Window (for testing) ──────────────────────────────────────────────

def reset_rate_window(username: str):
    """Clears request history for a user. Used in test setup/teardown."""
    _request_windows[username] = []


def get_all_rate_profiles() -> list[dict]:
    return [get_rate_profile(username) for username in _request_windows]
