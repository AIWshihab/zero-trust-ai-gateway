from app.core.policy_engine import evaluate_request


def test_research_context_only_tightens_thresholds():
    baseline = evaluate_request(
        model_risk_score=0.25,
        sensitivity_score=0.3,
        prompt_risk_score=0.2,
        request_rate_score=0.05,
        user_trust_penalty=0.1,
        secure_mode_enabled=False,
    )
    tightened = evaluate_request(
        model_risk_score=0.25,
        sensitivity_score=0.3,
        prompt_risk_score=0.2,
        request_rate_score=0.05,
        user_trust_penalty=0.1,
        secure_mode_enabled=False,
        attack_sequence_severity=0.85,
        repeated_pattern_count=5,
        cross_model_abuse_score=0.8,
    )

    assert tightened["effective_thresholds"]["challenge"] <= baseline["effective_thresholds"]["challenge"]
    assert tightened["effective_thresholds"]["block"] <= baseline["effective_thresholds"]["block"]
    assert "attack_sequence_escalation" in tightened["adaptive_reasons"]
    assert "repeated_blocked_pattern" in tightened["adaptive_reasons"]
    assert "cross_model_abuse_pattern_detected" in tightened["adaptive_reasons"]
    assert tightened["inputs"]["cross_model_abuse_score"] == 0.8
