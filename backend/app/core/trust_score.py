from collections import defaultdict

from app.schemas import RequestDecision

# username -> trust score (0.0 to 1.0, higher is better)
_user_trust_scores: dict[str, float] = defaultdict(lambda: 0.8)


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, value))


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

    if hasattr(decision, "value"):
        decision_value = decision.value
    else:
        decision_value = str(decision)

    if decision_value == "allow":
        current += 0.01
    elif decision_value == "challenge":
        current -= 0.04
    elif decision_value == "block":
        current -= 0.08

    current = _clamp(current)
    _user_trust_scores[username] = current
    return current


def reset_trust_score(username: str) -> float:
    _user_trust_scores[username] = 0.8
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