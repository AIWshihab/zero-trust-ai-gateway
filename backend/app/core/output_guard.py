from typing import Any


def inspect_output(text: str) -> dict[str, Any]:
    lowered = text.lower()

    findings: list[str] = []
    action = "allow"
    risk_score = 0.0

    suspicious_patterns = [
        "api key",
        "private key",
        "secret token",
        "password",
    ]

    for pattern in suspicious_patterns:
        if pattern in lowered:
            findings.append(f"Potential sensitive output pattern detected: {pattern}")
            risk_score += 25.0

    if risk_score >= 50.0:
        action = "block"
    elif risk_score > 0:
        action = "redact"

    return {
        "action": action,
        "risk_score": min(risk_score, 100.0),
        "findings": findings,
    }