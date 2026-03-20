from app.core.config import get_settings
from app.models.schemas import RequestDecision
from app.models.registry import get_model_risk_score, get_model_sensitivity_score

settings = get_settings()


# ─── Score Components ──────────────────────────────────────────────────────────

def calculate_security_score(
    model_id: int,
    prompt_risk_score: float,       # 0.0 - 1.0 (from prompt_guard)
    request_rate_score: float,      # 0.0 - 1.0 (from rate_limiter)
    user_trust_penalty: float,      # 0.0 - 1.0 (from trust_score)
) -> float:
    """
    Security Score = weighted sum of all risk factors.
    Higher score = higher risk = more likely to block.
    All inputs must be normalised between 0.0 and 1.0.
    """
    model_risk        = get_model_risk_score(model_id)
    data_sensitivity  = get_model_sensitivity_score(model_id)

    score = (
        (model_risk       * settings.WEIGHT_MODEL_RISK)        +
        (data_sensitivity * settings.WEIGHT_DATA_SENSITIVITY)  +
        (prompt_risk_score  * settings.WEIGHT_PROMPT_RISK)     +
        (request_rate_score * settings.WEIGHT_REQUEST_RATE)    +
        (user_trust_penalty * settings.WEIGHT_USER_TRUST_PENALTY)
    )

    return round(min(max(score, 0.0), 1.0), 4)  # clamp to [0.0, 1.0]


# ─── Decision Engine ───────────────────────────────────────────────────────────

def evaluate_decision(security_score: float) -> RequestDecision:
    """
    Maps security score to an enforcement decision:
      - BLOCK     : score >= TRUST_SCORE_BLOCK
      - CHALLENGE : score >= TRUST_SCORE_CHALLENGE
      - ALLOW     : score below both thresholds
    """
    if security_score >= settings.TRUST_SCORE_BLOCK:
        return RequestDecision.BLOCK
    elif security_score >= settings.TRUST_SCORE_CHALLENGE:
        return RequestDecision.CHALLENGE
    else:
        return RequestDecision.ALLOW


# ─── Reason Builder ────────────────────────────────────────────────────────────

def build_reason(
    security_score: float,
    decision: RequestDecision,
    model_id: int,
    prompt_risk_score: float,
    request_rate_score: float,
    user_trust_penalty: float,
) -> str:
    """
    Returns a human-readable explanation of why a decision was made.
    Useful for logging and the monitoring dashboard.
    """
    reasons = []

    if prompt_risk_score >= 0.7:
        reasons.append(f"high prompt risk ({prompt_risk_score:.2f})")
    if request_rate_score >= 0.7:
        reasons.append(f"excessive request rate ({request_rate_score:.2f})")
    if user_trust_penalty >= 0.7:
        reasons.append(f"low user trust ({user_trust_penalty:.2f})")
    if get_model_risk_score(model_id) >= 0.7:
        reasons.append("high-risk model")
    if get_model_sensitivity_score(model_id) >= 0.7:
        reasons.append("sensitive model data")

    reason_str = ", ".join(reasons) if reasons else "within acceptable thresholds"
    return f"Decision: {decision.value.upper()} | Score: {security_score} | Factors: {reason_str}"


# ─── Main Policy Evaluation Entry Point ───────────────────────────────────────

def evaluate_request(
    model_id: int,
    prompt_risk_score: float,
    request_rate_score: float,
    user_trust_penalty: float,
) -> dict:
    """
    Full policy evaluation pipeline.
    Returns score, decision, and reason — consumed by the gateway router.
    """
    security_score = calculate_security_score(
        model_id=model_id,
        prompt_risk_score=prompt_risk_score,
        request_rate_score=request_rate_score,
        user_trust_penalty=user_trust_penalty,
    )

    decision = evaluate_decision(security_score)

    reason = build_reason(
        security_score=security_score,
        decision=decision,
        model_id=model_id,
        prompt_risk_score=prompt_risk_score,
        request_rate_score=request_rate_score,
        user_trust_penalty=user_trust_penalty,
    )

    return {
        "security_score": security_score,
        "decision": decision,
        "reason": reason,
    }
