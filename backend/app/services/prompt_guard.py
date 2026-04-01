from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class GuardDecision(str, Enum):
    ALLOW = "allow"
    CHALLENGE = "challenge"
    BLOCK = "block"


@dataclass
class PromptGuardResult:
    decision: GuardDecision
    prompt_risk_score: float
    reason: str
    flags: list[str] = field(default_factory=list)
    static_score: float = 0.0


HIGH_RISK_PATTERNS = {
    "ignore previous instructions": 0.28,
    "ignore all instructions": 0.30,
    "disregard previous instructions": 0.28,
    "reveal your system prompt": 0.40,
    "print your hidden system prompt": 0.42,
    "show hidden prompt": 0.35,
    "hidden instructions": 0.26,
    "internal rules": 0.22,
    "developer message": 0.24,
    "system prompt": 0.30,
    "api key": 0.38,
    "secret token": 0.38,
    "private key": 0.42,
    "password": 0.28,
    "credential": 0.24,
    "bypass safety": 0.24,
    "disable safety": 0.26,
    "jailbreak": 0.24,
    "leak data": 0.22,
    "reveal secrets": 0.30,
    "dump secrets": 0.34,
    "extract secrets": 0.34,
}

MODERATE_RISK_PATTERNS = {
    "ignore instructions": 0.18,
    "override rules": 0.18,
    "do not follow safety": 0.20,
    "tell me your prompt": 0.20,
    "hidden prompt": 0.18,
    "secret": 0.12,
    "token": 0.10,
    "confidential": 0.12,
    "sensitive": 0.08,
    "bypass": 0.10,
}

SUSPICIOUS_COMBINATIONS = [
    (["ignore", "instructions"], 0.12, "instruction_override_combo"),
    (["system", "prompt"], 0.18, "system_prompt_combo"),
    (["api", "key"], 0.20, "api_key_combo"),
    (["secret", "token"], 0.20, "secret_token_combo"),
    (["private", "key"], 0.22, "private_key_combo"),
    (["reveal", "hidden"], 0.14, "reveal_hidden_combo"),
]


def _normalize(text: str) -> str:
    return " ".join(text.lower().strip().split())


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, value))


def _sensitivity_bonus(model_sensitivity: Optional[str]) -> float:
    normalized = str(model_sensitivity or "medium").lower()
    mapping = {
        "low": 0.00,
        "medium": 0.03,
        "high": 0.06,
        "critical": 0.10,
    }
    return mapping.get(normalized, 0.03)


def _user_penalty(user_trust_score: Optional[float]) -> float:
    if user_trust_score is None:
        return 0.0

    # assumes 0..1 scale where higher is better
    if user_trust_score >= 0.9:
        return -0.02
    if user_trust_score >= 0.75:
        return -0.01
    if user_trust_score >= 0.5:
        return 0.0
    if user_trust_score >= 0.3:
        return 0.04
    return 0.08


def _score_prompt(prompt: str) -> tuple[float, list[str]]:
    text = _normalize(prompt)
    score = 0.02
    flags: list[str] = []

    for pattern, weight in HIGH_RISK_PATTERNS.items():
        if pattern in text:
            score += weight
            flags.append(pattern)

    for pattern, weight in MODERATE_RISK_PATTERNS.items():
        if pattern in text:
            score += weight
            flags.append(pattern)

    for terms, weight, label in SUSPICIOUS_COMBINATIONS:
        if all(term in text for term in terms):
            score += weight
            flags.append(label)

    if len(text) > 800:
        score += 0.04
        flags.append("very_long_prompt")

    if text.count("ignore") >= 2:
        score += 0.08
        flags.append("repeated_ignore_language")

    if text.count("reveal") >= 2:
        score += 0.06
        flags.append("repeated_reveal_language")

    if any(word in text for word in ["api key", "private key", "secret token", "password"]):
        score += 0.10
        flags.append("credential_extraction_intent")

    if any(word in text for word in ["system prompt", "developer message", "hidden prompt"]):
        score += 0.12
        flags.append("prompt_extraction_intent")

    if any(word in text for word in ["bypass safety", "disable safety", "jailbreak"]):
        score += 0.12
        flags.append("safety_bypass_intent")

    return _clamp(score), sorted(set(flags))


async def evaluate_prompt_guard(
    prompt: str,
    user_trust_score: Optional[float] = None,
    model_sensitivity: Optional[str] = None,
    provider: Optional[str] = None,
) -> PromptGuardResult:
    static_score, flags = _score_prompt(prompt)

    final_score = static_score
    final_score += _sensitivity_bonus(model_sensitivity)
    final_score += _user_penalty(user_trust_score)

    provider_name = str(provider or "").lower()
    if provider_name in {"openai", "huggingface", "anthropic"}:
        final_score += 0.0

    final_score = _clamp(final_score)

    if final_score >= 0.55:
        decision = GuardDecision.BLOCK
        reason = (
            f"Prompt blocked due to high-risk prompt injection / secret extraction indicators. "
            f"static_score={round(static_score, 4)}"
        )
    elif final_score >= 0.35:
        decision = GuardDecision.CHALLENGE
        reason = (
            f"Prompt requires challenge due to moderate-risk indicators. "
            f"static_score={round(static_score, 4)}"
        )
    else:
        decision = GuardDecision.ALLOW
        reason = (
            f"Prompt allowed with low-to-moderate risk indicators. "
            f"static_score={round(static_score, 4)}"
        )

    return PromptGuardResult(
        decision=decision,
        prompt_risk_score=round(final_score, 4),
        reason=reason,
        flags=flags,
        static_score=round(static_score, 4),
    )


def analyze_prompt(prompt: str) -> dict:
    """
    Backward-compatible helper for any old routes still importing analyze_prompt().
    """
    score, flags = _score_prompt(prompt)

    if score >= 0.55:
        decision = "block"
        reason = "High-risk prompt injection / secret extraction indicators detected."
    elif score >= 0.35:
        decision = "challenge"
        reason = "Moderate-risk prompt detected."
    else:
        decision = "allow"
        reason = "Prompt appears benign under current policy."

    return {
        "risk_score": round(score, 4),
        "flags": flags,
        "decision": decision,
        "reason": reason,
    }