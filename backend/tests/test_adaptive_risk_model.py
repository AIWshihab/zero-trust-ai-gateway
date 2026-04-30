from app.core.adaptive_risk_model import (
    ADAPTIVE_RISK_WEIGHTS,
    build_adaptive_policy_state,
    compute_effective_risk,
    derive_control_effectiveness,
)
from app.core.policy_engine import evaluate_request
from app.schemas import RequestDecision


def test_effective_risk_is_deterministic_and_bounded():
    payload = {
        "base_model_risk": 0.72,
        "user_trust": 0.35,
        "attack_sequence_severity": 0.8,
        "cross_model_abuse_score": 0.7,
        "adaptive_policy_state": 0.6,
        "control_effectiveness": 0.2,
    }
    first = compute_effective_risk(**payload)
    second = compute_effective_risk(**payload)

    assert first == second
    assert 0.0 <= first["effective_risk"] <= 1.0
    assert round(sum(ADAPTIVE_RISK_WEIGHTS.values()), 4) == 1.0
    assert "weighted_contributions" in first
    assert "base risk high" in first["explanation"]


def test_control_effectiveness_derives_from_secured_risk():
    score = derive_control_effectiveness(base_model_risk=80, secured_model_risk=60)
    assert score == 0.25


def test_adaptive_policy_state_is_bounded():
    state = build_adaptive_policy_state(
        secure_mode_enabled=True,
        request_rate_score=0.9,
        recent_risky_events=12,
        recent_blocks=8,
        recent_challenges=10,
        research_threshold_pressure=0.8,
    )
    assert state == 1.0


def test_policy_engine_returns_effective_risk_explainability():
    result = evaluate_request(
        model_risk_score=0.72,
        sensitivity_score=0.5,
        prompt_risk_score=0.72,
        request_rate_score=0.4,
        user_trust_penalty=0.55,
        secure_mode_enabled=True,
        recent_risky_events=6,
        recent_blocks=3,
        recent_challenges=2,
        model_base_risk_score=72,
        secured_model_risk_score=60,
        attack_sequence_severity=0.85,
        repeated_pattern_count=5,
        cross_model_abuse_score=0.8,
    )

    assert result["decision"] in {RequestDecision.CHALLENGE, RequestDecision.BLOCK}
    assert "effective_risk" in result
    assert "effective_risk_model" in result
    assert "weighted_contributions" in result["effective_risk_model"]
    assert "Decision" in result["effective_risk_explanation"]
