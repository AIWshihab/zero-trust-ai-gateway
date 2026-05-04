import re
from dataclasses import dataclass


@dataclass(frozen=True)
class SensitivityResult:
    level: str
    score: float
    findings: list[str]


SENSITIVITY_PATTERNS: list[tuple[str, str, float]] = [
    ("secret", r"\b(api[_-]?key|secret[_-]?key|bearer\s+[a-z0-9._~+/=-]{16,}|github[_-]?token|hf_[a-z0-9]{20,})\b", 1.0),
    ("credential", r"\b(password|passwd|pwd)\s*[:=]\s*[^\s]{6,}", 0.9),
    ("private_key", r"-----BEGIN (RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----", 1.0),
    ("email", r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", 0.45),
    ("phone", r"\b(?:\+?1[-.\s]?)?\(?[2-9]\d{2}\)?[-.\s]?[2-9]\d{2}[-.\s]?\d{4}\b", 0.55),
    ("ssn", r"\b\d{3}-\d{2}-\d{4}\b", 0.95),
    ("credit_card", r"\b(?:\d[ -]*?){13,16}\b", 0.85),
    ("ip_address", r"\b(?:\d{1,3}\.){3}\d{1,3}\b", 0.35),
]


def classify_data_sensitivity(text: str) -> SensitivityResult:
    raw = text or ""
    findings: list[str] = []
    score = 0.0

    for label, pattern, weight in SENSITIVITY_PATTERNS:
        if re.search(pattern, raw, flags=re.IGNORECASE):
            findings.append(label)
            score = max(score, weight)

    if len(findings) >= 3:
        score = max(score, 0.9)
    elif len(findings) >= 2:
        score = max(score, 0.7)

    if score >= 0.9:
        level = "CRITICAL"
    elif score >= 0.7:
        level = "HIGH"
    elif score >= 0.4:
        level = "MEDIUM"
    else:
        level = "LOW"

    return SensitivityResult(level=level, score=round(score, 4), findings=findings)
