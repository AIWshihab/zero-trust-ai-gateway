import re
from typing import Any

from app.models.security import DetectionRule
from app.schemas import RequestDecision
from app.services.security_catalog import match_dynamic_rules


SECRET_PATTERNS: list[tuple[str, str, float]] = [
    (r"sk-[A-Za-z0-9_\-]{20,}", "openai_api_key", 35.0),
    (r"hf_[A-Za-z0-9]{20,}", "huggingface_token", 35.0),
    (r"AKIA[0-9A-Z]{16}", "aws_access_key", 35.0),
    (r"-----BEGIN [A-Z ]*PRIVATE KEY-----", "private_key_block", 50.0),
    (r"eyJ[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}", "jwt_token", 30.0),
    (r"(?i)(api[_ -]?key|secret[_ -]?token|password|credential)\s*[:=]\s*['\"]?[^'\"\s]{8,}", "named_secret", 30.0),
]

PII_PATTERNS: list[tuple[str, str, float]] = [
    (r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b", "email_address", 10.0),
    (r"\b(?:\+?\d[\d\s().-]{7,}\d)\b", "phone_like_number", 8.0),
]


def _redact_patterns(text: str, patterns: list[tuple[str, str, float]], findings: list[str]) -> tuple[str, float]:
    risk_score = 0.0
    redacted = text

    for pattern, label, weight in patterns:
        matches = list(re.finditer(pattern, redacted))
        if not matches:
            continue
        findings.append(f"Sensitive output pattern detected: {label}")
        risk_score += min(weight * len(matches), weight * 3)
        redacted = re.sub(pattern, f"[REDACTED:{label}]", redacted)

    return redacted, risk_score


def inspect_output(text: str, dynamic_rules: list[DetectionRule] | None = None) -> dict[str, Any]:
    lowered = text.lower()

    findings: list[str] = []
    action = "allow"
    risk_score = 0.0
    redacted_text = text

    suspicious_patterns = [
        "api key",
        "private key",
        "secret token",
        "password",
        "access token",
        "bearer token",
        ".env",
    ]

    for pattern in suspicious_patterns:
        if pattern in lowered:
            findings.append(f"Potential sensitive output pattern detected: {pattern}")
            risk_score += 25.0

    redacted_text, secret_risk = _redact_patterns(redacted_text, SECRET_PATTERNS, findings)
    risk_score += secret_risk
    redacted_text, pii_risk = _redact_patterns(redacted_text, PII_PATTERNS, findings)
    risk_score += pii_risk
    dynamic_result = match_dynamic_rules(text, dynamic_rules or [])
    risk_score += float(dynamic_result.get("risk_delta", 0.0)) * 100.0
    for flag in dynamic_result.get("flags", []):
        findings.append(f"Dynamic output rule matched: {flag}")

    forced_decision = dynamic_result.get("forced_decision", RequestDecision.ALLOW)
    if forced_decision == RequestDecision.BLOCK or risk_score >= 50.0:
        action = "block"
    elif forced_decision == RequestDecision.CHALLENGE or risk_score > 0:
        action = "redact"

    return {
        "action": action,
        "risk_score": min(risk_score, 100.0),
        "findings": findings,
        "redacted_text": redacted_text,
        "dynamic_rule_matches": dynamic_result.get("matches", []),
    }
