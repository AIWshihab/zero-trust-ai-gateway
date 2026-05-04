from __future__ import annotations

from typing import Any


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return round(float(value), 4)
    except Exception:
        return round(float(default), 4)


def _decision_value(value: Any) -> str:
    if hasattr(value, "value"):
        return str(value.value)
    return str(value or "allow").lower()


def build_decision_explanation(
    *,
    decision: Any,
    reason: str | None,
    policy_result: dict[str, Any] | None = None,
    prompt_guard_result: Any | None = None,
    data_sensitivity: Any | None = None,
    output_guard_result: dict[str, Any] | None = None,
    forwarded: bool = False,
) -> dict[str, Any]:
    policy_result = policy_result or {}
    inputs = dict(policy_result.get("inputs") or {})
    thresholds = dict(policy_result.get("effective_thresholds") or {})
    decision_value = _decision_value(decision)

    factors = {
        "prompt_risk": _safe_float(
            getattr(prompt_guard_result, "prompt_risk_score", None),
            inputs.get("prompt_risk_score", 0.0),
        ),
        "user_trust": round(1.0 - _safe_float(inputs.get("effective_user_trust_penalty", inputs.get("user_trust_penalty", 0.0))), 4),
        "model_risk": _safe_float(inputs.get("model_risk_score", 0.0)),
        "request_frequency": _safe_float(inputs.get("request_rate_score", 0.0)),
        "sensitivity": _safe_float(inputs.get("sensitivity_score", 0.0)),
        "effective_risk": _safe_float(policy_result.get("effective_risk", 0.0)),
    }

    if data_sensitivity is not None:
        factors["data_sensitivity"] = _safe_float(getattr(data_sensitivity, "score", 0.0))
    if output_guard_result:
        factors["output_risk"] = round(_safe_float(output_guard_result.get("risk_score", 0.0)) / 100.0, 4)

    high_factors = []
    if factors["prompt_risk"] >= 0.55:
        high_factors.append("high prompt injection or abuse risk")
    if factors["user_trust"] <= 0.45:
        high_factors.append("low trust score")
    if factors["model_risk"] >= 0.65:
        high_factors.append("elevated model posture risk")
    if factors["request_frequency"] >= 0.65:
        high_factors.append("abnormal request frequency")
    if factors["sensitivity"] >= 0.70:
        high_factors.append("high data or model sensitivity")
    if factors["effective_risk"] >= 0.65:
        high_factors.append("high formal effective risk")

    if decision_value == "block":
        summary = "Request blocked due to combined high-risk indicators."
    elif decision_value == "challenge":
        summary = "Request challenged because the gateway detected moderate risk that needs additional verification."
    else:
        summary = "Request allowed because observed risk stayed within adaptive policy thresholds."

    if high_factors:
        summary = f"{summary} Key drivers: {', '.join(high_factors)}."

    return {
        "factors": factors,
        "explanation": summary,
        "decision_trace": {
            "pdp": "app.core.policy_engine.evaluate_request",
            "pep_forwarded": bool(forwarded),
            "thresholds": thresholds,
            "policy_inputs": inputs,
            "adaptive_reasons": list(policy_result.get("adaptive_reasons") or []),
            "prompt_guard": {
                "decision": _decision_value(getattr(prompt_guard_result, "decision", None)),
                "flags": list(getattr(prompt_guard_result, "flags", []) or []),
                "reason": getattr(prompt_guard_result, "reason", None),
            },
            "data_sensitivity": {
                "level": getattr(data_sensitivity, "level", None),
                "score": getattr(data_sensitivity, "score", None),
                "findings": list(getattr(data_sensitivity, "findings", []) or []),
            },
            "output_guard": output_guard_result or {},
        },
    }


def simple_decision_explanation(
    *,
    decision: Any,
    reason: str | None,
    security_score: float = 0.0,
    prompt_risk_score: float = 0.0,
    effective_risk: float | None = None,
    forwarded: bool = False,
) -> dict[str, Any]:
    value = _decision_value(decision)
    risk = _safe_float(effective_risk if effective_risk is not None else security_score)
    factors = {
        "prompt_risk": _safe_float(prompt_risk_score),
        "user_trust": 0.0,
        "model_risk": 0.0,
        "request_frequency": 0.0,
        "sensitivity": 0.0,
        "effective_risk": risk,
    }
    if value == "block":
        explanation = reason or "Request blocked by an enforcement pre-check."
    elif value == "challenge":
        explanation = reason or "Request challenged by an enforcement pre-check."
    else:
        explanation = reason or "Request allowed by the gateway."
    return {
        "factors": factors,
        "explanation": explanation,
        "decision_trace": {
            "pdp": "precheck",
            "pep_forwarded": bool(forwarded),
            "policy_inputs": factors,
            "adaptive_reasons": [],
        },
    }
