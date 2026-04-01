from typing import Any


def compute_protected_score(
    *,
    base_trust_score: float,
    require_auth: bool = True,
    prompt_filtering: bool = True,
    output_filtering: bool = True,
    logging_enabled: bool = True,
    anomaly_detection: bool = True,
    rate_limit_enabled: bool = True,
) -> dict[str, Any]:
    bonus = 0.0
    active_controls: list[str] = []

    if require_auth:
        bonus += 8.0
        active_controls.append("Authentication")

    if prompt_filtering:
        bonus += 10.0
        active_controls.append("Prompt Filtering")

    if output_filtering:
        bonus += 10.0
        active_controls.append("Output Filtering")

    if logging_enabled:
        bonus += 6.0
        active_controls.append("Audit Logging")

    if anomaly_detection:
        bonus += 8.0
        active_controls.append("Anomaly Detection")

    if rate_limit_enabled:
        bonus += 6.0
        active_controls.append("Rate Limiting")

    protected_score = min(100.0, float(base_trust_score) + bonus)

    return {
        "base_trust_score": float(base_trust_score),
        "protected_score": protected_score,
        "improvement_delta": protected_score - float(base_trust_score),
        "active_controls": active_controls,
    }