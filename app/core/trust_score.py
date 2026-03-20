from datetime import datetime, timedelta
from collections import defaultdict
from app.models.schemas import RequestDecision

# ─── In-Memory Trust Store (swap for DB in Stage 4) ──────────────────────────

# Structure: { username: { "score": float, "history": [...] } }
_trust_store: dict[str, dict] = defaultdict(lambda: {
    "score":            1.0,   # starts at full trust
    "blocked_count":    0,
    "challenged_count": 0,
    "total_requests":   0,
    "last_updated":     datetime.utcnow().isoformat(),
    "history":          [],    # list of recent decisions
})

# ─── Config ───────────────────────────────────────────────────────────────────

MAX_HISTORY         = 50      # decisions to keep per user
BLOCK_PENALTY       = 0.15    # trust deducted per block
CHALLENGE_PENALTY   = 0.05    # trust deducted per challenge
RECOVERY_RATE       = 0.01    # trust recovered per allowed request
MIN_TRUST           = 0.0
MAX_TRUST           = 1.0


# ─── Update Trust After Each Request ─────────────────────────────────────────

def update_trust_score(username: str, decision: RequestDecision) -> float:
    """
    Adjusts user trust score based on the ZTA decision outcome.
    Called after every request is evaluated.
    """
    user = _trust_store[username]
    current_score = user["score"]

    if decision == RequestDecision.BLOCK:
        new_score = current_score - BLOCK_PENALTY
        user["blocked_count"] += 1

    elif decision == RequestDecision.CHALLENGE:
        new_score = current_score - CHALLENGE_PENALTY
        user["challenged_count"] += 1

    else:  # ALLOW
        new_score = current_score + RECOVERY_RATE

    # Clamp score to [0.0, 1.0]
    user["score"] = round(min(max(new_score, MIN_TRUST), MAX_TRUST), 4)
    user["total_requests"] += 1
    user["last_updated"] = datetime.utcnow().isoformat()

    # Append to history (keep last MAX_HISTORY entries)
    user["history"].append({
        "decision":  decision.value,
        "score":     user["score"],
        "timestamp": datetime.utcnow().isoformat(),
    })
    if len(user["history"]) > MAX_HISTORY:
        user["history"].pop(0)

    return user["score"]


# ─── Get Trust Penalty for Policy Engine ─────────────────────────────────────

def get_user_trust_penalty(username: str) -> float:
    """
    Returns a normalised penalty score [0.0 - 1.0].
    High trust = low penalty. Low trust = high penalty.
    Consumed directly by policy_engine.py.

    penalty = 1.0 - trust_score
    """
    trust_score = _trust_store[username]["score"]
    return round(1.0 - trust_score, 4)


# ─── Get Full Trust Profile ───────────────────────────────────────────────────

def get_trust_profile(username: str) -> dict:
    """
    Returns full trust profile for a user.
    Used by monitoring dashboard and /me endpoint.
    """
    user = _trust_store[username]
    return {
        "username":         username,
        "trust_score":      user["score"],
        "trust_penalty":    get_user_trust_penalty(username),
        "blocked_count":    user["blocked_count"],
        "challenged_count": user["challenged_count"],
        "total_requests":   user["total_requests"],
        "last_updated":     user["last_updated"],
        "recent_history":   user["history"][-10:],  # last 10 decisions
    }


# ─── Reset Trust (admin use) ──────────────────────────────────────────────────

def reset_trust_score(username: str) -> float:
    """
    Resets a user's trust score back to 1.0.
    Admin action — useful for testing and dispute resolution.
    """
    _trust_store[username]["score"]            = 1.0
    _trust_store[username]["blocked_count"]    = 0
    _trust_store[username]["challenged_count"] = 0
    _trust_store[username]["history"]          = []
    _trust_store[username]["last_updated"]     = datetime.utcnow().isoformat()
    return 1.0


# ─── Get All Trust Profiles (admin use) ──────────────────────────────────────

def get_all_trust_profiles() -> list[dict]:
    return [get_trust_profile(username) for username in _trust_store]
