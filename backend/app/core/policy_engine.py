from app.core.config import get_settings
from app.schemas import RequestDecision

settings = get_settings()


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, value))


def _safe_count(value) -> int:
    try:
        return max(0, int(value))
    except Exception:
        return 0


def _normalize_model_base_risk(model_base_risk_score) -> float | None:
    if model_base_risk_score is None:
        return None

    try:
        raw = float(model_base_risk_score)
    except Exception:
        return None

    if raw <= 1.0:
        raw *= 100.0

    return max(0.0, min(100.0, raw))


def _secure_mode_adjustments(
    *,
    secure_mode_enabled: bool,
    prompt_risk_score: float,
    request_rate_score: float,
    user_trust_penalty: float,
    recent_risky_events: int,
    recent_blocks: int,
    recent_challenges: int,
    model_base_risk_score: float | None,
) -> dict:
    base_challenge = _clamp(settings.TRUST_SCORE_CHALLENGE)
    base_block = _clamp(settings.TRUST_SCORE_BLOCK)

    effective_challenge = base_challenge
    effective_block = base_block
    trust_penalty_multiplier = 1.0
    adaptive_reasons: list[str] = []

    if not secure_mode_enabled:
        return {
            "effective_challenge_threshold": round(effective_challenge, 4),
            "effective_block_threshold": round(effective_block, 4),
            "trust_penalty_multiplier": round(trust_penalty_multiplier, 4),
            "adaptive_reasons": adaptive_reasons,
        }

    context_pressure = 0.03
    adaptive_reasons.append("secure mode baseline hardening applied")

    if prompt_risk_score >= 0.75:
        context_pressure += 0.10
        adaptive_reasons.append("very high prompt risk tightened thresholds")
    elif prompt_risk_score >= 0.55:
        context_pressure += 0.06
        adaptive_reasons.append("elevated prompt risk tightened thresholds")
    elif prompt_risk_score >= 0.40:
        context_pressure += 0.03
        adaptive_reasons.append("moderate prompt risk tightened thresholds")

    if user_trust_penalty >= 0.55:
        context_pressure += 0.08
        trust_penalty_multiplier += 0.25
        adaptive_reasons.append("low user trust increased penalties")
    elif user_trust_penalty >= 0.35:
        context_pressure += 0.05
        trust_penalty_multiplier += 0.14
        adaptive_reasons.append("moderate user trust increased penalties")

    if recent_risky_events >= 6:
        context_pressure += 0.09
        trust_penalty_multiplier += 0.16
        adaptive_reasons.append("repeated recent risky activity escalated enforcement")
    elif recent_risky_events >= 3:
        context_pressure += 0.06
        trust_penalty_multiplier += 0.1
        adaptive_reasons.append("multiple recent risky events tightened controls")
    elif recent_risky_events >= 1:
        context_pressure += 0.03
        adaptive_reasons.append("recent risky event triggered mild escalation")

    if recent_blocks >= 2:
        context_pressure += 0.08
        trust_penalty_multiplier += 0.16
        adaptive_reasons.append("recent repeated block outcomes escalated quickly")
    elif recent_blocks == 1:
        context_pressure += 0.04
        trust_penalty_multiplier += 0.08
        adaptive_reasons.append("recent block outcome increased strictness")

    if recent_challenges >= 4:
        context_pressure += 0.06
        trust_penalty_multiplier += 0.1
        adaptive_reasons.append("frequent challenge outcomes tightened controls")
    elif recent_challenges >= 2:
        context_pressure += 0.03
        trust_penalty_multiplier += 0.06
        adaptive_reasons.append("multiple challenge outcomes tightened controls")

    if request_rate_score >= 0.65:
        context_pressure += 0.05
        adaptive_reasons.append("high request-rate pressure tightened thresholds")

    if model_base_risk_score is not None:
        if model_base_risk_score >= 70.0:
            context_pressure += 0.07
            adaptive_reasons.append("high model base risk tightened secure-mode thresholds")
        elif model_base_risk_score >= 50.0:
            context_pressure += 0.04
            adaptive_reasons.append("moderate model base risk tightened secure-mode thresholds")

    challenge_tightening = min(0.20, context_pressure)
    block_tightening = min(0.18, context_pressure * 0.9)

    effective_challenge = max(0.2, base_challenge - challenge_tightening)
    effective_block = max(effective_challenge + 0.05, base_block - block_tightening)

    trust_penalty_multiplier = max(1.0, min(1.8, trust_penalty_multiplier))

    return {
        "effective_challenge_threshold": round(effective_challenge, 4),
        "effective_block_threshold": round(effective_block, 4),
        "trust_penalty_multiplier": round(trust_penalty_multiplier, 4),
        "adaptive_reasons": adaptive_reasons,
    }


def evaluate_request(
    *,
    model_risk_score: float,
    sensitivity_score: float,
    prompt_risk_score: float,
    request_rate_score: float,
    user_trust_penalty: float,
    secure_mode_enabled: bool = False,
    recent_risky_events: int = 0,
    recent_blocks: int = 0,
    recent_challenges: int = 0,
    model_base_risk_score: float | None = None,
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
    recent_risky_events = _safe_count(recent_risky_events)
    recent_blocks = _safe_count(recent_blocks)
    recent_challenges = _safe_count(recent_challenges)
    normalized_model_base_risk = _normalize_model_base_risk(model_base_risk_score)

    secure_mode_context = _secure_mode_adjustments(
        secure_mode_enabled=bool(secure_mode_enabled),
        prompt_risk_score=prompt_risk_score,
        request_rate_score=request_rate_score,
        user_trust_penalty=user_trust_penalty,
        recent_risky_events=recent_risky_events,
        recent_blocks=recent_blocks,
        recent_challenges=recent_challenges,
        model_base_risk_score=normalized_model_base_risk,
    )

    effective_challenge_threshold = float(secure_mode_context["effective_challenge_threshold"])
    effective_block_threshold = float(secure_mode_context["effective_block_threshold"])
    trust_penalty_multiplier = float(secure_mode_context["trust_penalty_multiplier"])
    adaptive_reasons = list(secure_mode_context["adaptive_reasons"])

    effective_user_trust_penalty = _clamp(user_trust_penalty * trust_penalty_multiplier)

    security_score = (
        settings.WEIGHT_MODEL_RISK * model_risk_score
        + settings.WEIGHT_DATA_SENSITIVITY * sensitivity_score
        + settings.WEIGHT_PROMPT_RISK * prompt_risk_score
        + settings.WEIGHT_REQUEST_RATE * request_rate_score
        + settings.WEIGHT_USER_TRUST_PENALTY * effective_user_trust_penalty
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
    if effective_user_trust_penalty >= 0.5:
        factors.append(f"low user trust ({effective_user_trust_penalty:.2f})")
    if bool(secure_mode_enabled) and adaptive_reasons:
        factors.append("secure mode adaptive hardening active")

    if security_score >= effective_block_threshold:
        decision = RequestDecision.BLOCK
    elif security_score >= effective_challenge_threshold:
        decision = RequestDecision.CHALLENGE
    else:
        decision = RequestDecision.ALLOW

    thresholds_text = (
        f"Thresholds: challenge>={round(effective_challenge_threshold, 4)}, "
        f"block>={round(effective_block_threshold, 4)}"
    )

    if factors:
        reason = (
            f"Decision: {decision.value.upper()} | "
            f"Score: {round(security_score, 4)} | "
            f"{thresholds_text} | "
            f"Factors: {', '.join(factors)}"
        )
    else:
        reason = (
            f"Decision: {decision.value.upper()} | "
            f"Score: {round(security_score, 4)} | "
            f"{thresholds_text} | "
            f"Factors: within acceptable thresholds"
        )

    if adaptive_reasons:
        reason = f"{reason} | Adaptive: {'; '.join(adaptive_reasons)}"

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
            "effective_user_trust_penalty": round(effective_user_trust_penalty, 4),
            "trust_penalty_multiplier": round(trust_penalty_multiplier, 4),
            "recent_risky_events": recent_risky_events,
            "recent_blocks": recent_blocks,
            "recent_challenges": recent_challenges,
            "model_base_risk_score": (
                round(normalized_model_base_risk, 2)
                if normalized_model_base_risk is not None
                else None
            ),
            "secure_mode_enabled": bool(secure_mode_enabled),
        },
        "effective_thresholds": {
            "challenge": round(effective_challenge_threshold, 4),
            "block": round(effective_block_threshold, 4),
            "baseline_challenge": round(_clamp(settings.TRUST_SCORE_CHALLENGE), 4),
            "baseline_block": round(_clamp(settings.TRUST_SCORE_BLOCK), 4),
        },
        "adaptive_reasons": adaptive_reasons,
    }
