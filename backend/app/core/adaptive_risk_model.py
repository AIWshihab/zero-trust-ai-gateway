from __future__ import annotations

from typing import Any

ADAPTIVE_RISK_WEIGHTS: dict[str, float] = {
    "base_model_risk": 0.30,
    "user_trust_risk": 0.20,
    "attack_sequence_severity": 0.18,
    "cross_model_abuse_score": 0.14,
    "adaptive_policy_state": 0.10,
    "control_gap": 0.08,
}


def _clamp_01(value: Any) -> float:
    try:
        raw = float(value)
    except Exception:
        raw = 0.0
    return max(0.0, min(1.0, raw))


def normalize_risk(value: Any) -> float:
    risk = _clamp_01(value)
    try:
        raw = float(value)
    except Exception:
        return risk
    if raw > 1.0:
        risk = max(0.0, min(100.0, raw)) / 100.0
    return round(risk, 4)


def derive_control_effectiveness(
    *,
    base_model_risk: float | None,
    secured_model_risk: float | None = None,
    explicit_control_effectiveness: float | None = None,
) -> float:
    if explicit_control_effectiveness is not None:
        return round(_clamp_01(explicit_control_effectiveness), 4)

    base = normalize_risk(base_model_risk)
    secured = normalize_risk(secured_model_risk)
    if base <= 0.0 or secured_model_risk is None:
        return 0.0
    return round(_clamp_01((base - secured) / base), 4)


def build_adaptive_policy_state(
    *,
    secure_mode_enabled: bool,
    request_rate_score: float,
    recent_risky_events: int,
    recent_blocks: int,
    recent_challenges: int,
    research_threshold_pressure: float = 0.0,
) -> float:
    pressure = 0.0
    if secure_mode_enabled:
        pressure += 0.20
    pressure += _clamp_01(request_rate_score) * 0.25
    pressure += min(1.0, max(0, int(recent_risky_events)) / 6.0) * 0.20
    pressure += min(1.0, max(0, int(recent_blocks)) / 3.0) * 0.20
    pressure += min(1.0, max(0, int(recent_challenges)) / 5.0) * 0.10
    pressure += _clamp_01(research_threshold_pressure) * 0.50
    return round(_clamp_01(pressure), 4)


def compute_effective_risk(
    *,
    base_model_risk: float,
    user_trust: float,
    attack_sequence_severity: float,
    cross_model_abuse_score: float,
    adaptive_policy_state: float,
    control_effectiveness: float,
) -> dict[str, Any]:
    base_risk = normalize_risk(base_model_risk)
    trust = _clamp_01(user_trust)
    trust_risk = round(1.0 - trust, 4)
    attack = _clamp_01(attack_sequence_severity)
    cross_model = _clamp_01(cross_model_abuse_score)
    adaptive = _clamp_01(adaptive_policy_state)
    control = _clamp_01(control_effectiveness)
    control_gap = round(1.0 - control, 4)

    normalized_components = {
        "base_model_risk": base_risk,
        "user_trust": round(trust, 4),
        "user_trust_risk": trust_risk,
        "attack_sequence_severity": round(attack, 4),
        "cross_model_abuse_score": round(cross_model, 4),
        "adaptive_policy_state": round(adaptive, 4),
        "control_effectiveness": round(control, 4),
        "control_gap": control_gap,
    }

    weighted_contributions = {
        "base_model_risk": round(base_risk * ADAPTIVE_RISK_WEIGHTS["base_model_risk"], 4),
        "user_trust_risk": round(trust_risk * ADAPTIVE_RISK_WEIGHTS["user_trust_risk"], 4),
        "attack_sequence_severity": round(attack * ADAPTIVE_RISK_WEIGHTS["attack_sequence_severity"], 4),
        "cross_model_abuse_score": round(cross_model * ADAPTIVE_RISK_WEIGHTS["cross_model_abuse_score"], 4),
        "adaptive_policy_state": round(adaptive * ADAPTIVE_RISK_WEIGHTS["adaptive_policy_state"], 4),
        "control_gap": round(control_gap * ADAPTIVE_RISK_WEIGHTS["control_gap"], 4),
    }
    effective_risk = round(_clamp_01(sum(weighted_contributions.values())), 4)

    explanation_bits: list[str] = []
    if base_risk >= 0.70:
        explanation_bits.append(f"base risk high ({base_risk:.2f})")
    elif base_risk >= 0.45:
        explanation_bits.append(f"base risk moderate ({base_risk:.2f})")
    else:
        explanation_bits.append(f"base risk controlled ({base_risk:.2f})")

    if trust <= 0.45:
        explanation_bits.append(f"user trust low ({trust:.2f})")
    elif trust <= 0.70:
        explanation_bits.append(f"user trust moderate ({trust:.2f})")
    else:
        explanation_bits.append(f"user trust strong ({trust:.2f})")

    if attack >= 0.70:
        explanation_bits.append("attack sequence severe")
    elif attack >= 0.35:
        explanation_bits.append("attack sequence suspicious")

    if cross_model >= 0.55:
        explanation_bits.append("cross-model abuse detected")

    if adaptive >= 0.45:
        explanation_bits.append("adaptive policy pressure elevated")

    if control < 0.15:
        explanation_bits.append("control reduction insufficient")
    elif control >= 0.35:
        explanation_bits.append("control effectiveness materially reduces risk")

    return {
        "effective_risk": effective_risk,
        "weights": ADAPTIVE_RISK_WEIGHTS,
        "normalized_components": normalized_components,
        "weighted_contributions": weighted_contributions,
        "explanation": "Effective risk "
        + f"{effective_risk:.2f} from "
        + ", ".join(explanation_bits)
        + ".",
    }
