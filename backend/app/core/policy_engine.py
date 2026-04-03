from app.core.config import get_settings
from app.schemas import RequestDecision

settings = get_settings()


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, value))


def evaluate_request(
    *,
    model_risk_score: float,
    sensitivity_score: float,
    prompt_risk_score: float,
    request_rate_score: float,
    user_trust_penalty: float,
) -> dict:
    """
    Final weighted policy decision.
    All inputs are expected on 0.0 to 1.0 scale.
    """

    model_risk_score = _clamp(model_risk_score)
    sensitivity_score = _clamp(sensitivity_score)
    prompt_risk_score = _clamp(prompt_risk_score)
    request_rate_score = _clamp(request_rate_score)
    user_trust_penalty = _clamp(user_trust_penalty)

    security_score = (
        settings.WEIGHT_MODEL_RISK * model_risk_score
        + settings.WEIGHT_DATA_SENSITIVITY * sensitivity_score
        + settings.WEIGHT_PROMPT_RISK * prompt_risk_score
        + settings.WEIGHT_REQUEST_RATE * request_rate_score
        + settings.WEIGHT_USER_TRUST_PENALTY * user_trust_penalty
    )

    security_score = _clamp(security_score)

    factors: list[str] = []

    if model_risk_score >= 0.7:
        factors.append(f"high model risk ({model_risk_score:.2f})")
    if sensitivity_score >= 0.7:
        factors.append(f"high model sensitivity ({sensitivity_score:.2f})")
    if prompt_risk_score >= 0.5:
        factors.append(f"high prompt risk ({prompt_risk_score:.2f})")
    if request_rate_score >= 0.5:
        factors.append(f"high request rate ({request_rate_score:.2f})")
    if user_trust_penalty >= 0.5:
        factors.append(f"low user trust ({user_trust_penalty:.2f})")

    if security_score >= settings.TRUST_SCORE_BLOCK:
        decision = RequestDecision.BLOCK
    elif security_score >= settings.TRUST_SCORE_CHALLENGE:
        decision = RequestDecision.CHALLENGE
    else:
        decision = RequestDecision.ALLOW

    if factors:
        reason = (
            f"Decision: {decision.value.upper()} | "
            f"Score: {round(security_score, 4)} | "
            f"Factors: {', '.join(factors)}"
        )
    else:
        reason = (
            f"Decision: {decision.value.upper()} | "
            f"Score: {round(security_score, 4)} | "
            f"Factors: within acceptable thresholds"
        )

    return {
        "decision": decision,
        "security_score": round(security_score, 4),
        "reason": reason,
        "inputs": {
            "model_risk_score": round(model_risk_score, 4),
            "sensitivity_score": round(sensitivity_score, 4),
            "prompt_risk_score": round(prompt_risk_score, 4),
            "request_rate_score": round(request_rate_score, 4),
            "user_trust_penalty": round(user_trust_penalty, 4),
        },
    }