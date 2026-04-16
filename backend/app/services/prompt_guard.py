from dataclasses import dataclass, field
from enum import Enum
import re
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


INJECTION_PATTERNS: list[tuple[str, float, str]] = [
    (r"ignore (all|previous|prior) instructions", 0.28, "injection_ignore_instructions"),
    (r"disregard (the )?(rules|guardrails|safety)", 0.26, "injection_disregard_rules"),
    (r"override (the )?(system|developer|safety)", 0.24, "injection_override"),
    (r"you are now", 0.12, "injection_role_rewrite"),
    (r"act as", 0.10, "injection_act_as"),
    (r"jailbreak", 0.30, "injection_jailbreak"),
    (r"do anything now", 0.30, "injection_dan"),
    (r"bypass safety", 0.24, "injection_bypass_safety"),
    (r"disable safety", 0.24, "injection_disable_safety"),
]


EXTRACTION_PATTERNS: list[tuple[str, float, str]] = [
    (r"(reveal|show|print|repeat).{0,24}(system prompt|hidden prompt|developer message)", 0.38, "extraction_prompt_leak"),
    (r"what (is|are) your (system prompt|instructions|hidden rules)", 0.34, "extraction_system_question"),
    (r"(api key|secret token|private key|password|credentials)", 0.32, "extraction_credential_target"),
    (r"dump (secrets|tokens|credentials)", 0.34, "extraction_dump_secrets"),
    (r"extract (secrets|credentials|keys)", 0.34, "extraction_extract_secrets"),
]


HARMFUL_PATTERNS: list[tuple[str, float, str]] = [
    (r"how to (make|build|create|assemble).{0,24}(bomb|explosive)", 0.70, "harmful_explosives"),
    (r"how to (make|build|create|assemble).{0,24}(gun|firearm|rifle|pistol|shotgun)", 0.70, "harmful_firearm_construction"),
    (r"(ghost gun|3d[- ]?printed gun)", 0.68, "harmful_ghost_gun"),
    (r"(write|create|build).{0,20}(malware|ransomware|virus|exploit)", 0.66, "harmful_malware"),
    (r"(ddos|botnet|sql injection|xss|privilege escalation)", 0.58, "harmful_cyber_abuse"),
    (r"(steal|exfiltrate|dump).{0,24}(passwords|tokens|credentials|database)", 0.58, "harmful_data_theft"),
    (r"(child|minor).{0,24}(sexual|explicit|nude)", 0.80, "harmful_minor_sexual_content"),
    (r"(sexual|nude).{0,24}(child|minor)", 0.80, "harmful_minor_sexual_content_reverse"),
]


HIGH_RISK_KEYWORDS = [
    "how to make a gun",
    "make me a gun",
    "how to build a bomb",
    "how to make a bomb",
    "write ransomware",
    "create malware",
    "bypass safety filters",
    "ignore all instructions",
    "reveal system prompt",
]


SUSPICIOUS_TERM_COMBINATIONS: list[tuple[list[str], float, str]] = [
    (["ignore", "instructions"], 0.10, "combo_ignore_instructions"),
    (["system", "prompt"], 0.14, "combo_system_prompt"),
    (["api", "key"], 0.16, "combo_api_key"),
    (["secret", "token"], 0.16, "combo_secret_token"),
    (["private", "key"], 0.18, "combo_private_key"),
]


def _normalize(text: str) -> str:
    return " ".join(text.lower().strip().split())


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, value))


def _dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        ordered.append(value)
    return ordered


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

    trust = _clamp(float(user_trust_score))
    if trust >= 0.90:
        return -0.02
    if trust >= 0.75:
        return -0.01
    if trust >= 0.55:
        return 0.0
    if trust >= 0.35:
        return 0.05
    return 0.10


def _apply_patterns(text: str, patterns: list[tuple[str, float, str]], flags: list[str]) -> tuple[float, int]:
    score_delta = 0.0
    hits = 0
    for pattern, weight, label in patterns:
        if re.search(pattern, text):
            score_delta += weight
            flags.append(label)
            hits += 1
    return score_delta, hits


def _score_prompt(prompt: str) -> tuple[float, list[str]]:
    text = _normalize(prompt)
    score = 0.01
    flags: list[str] = []

    injection_score, injection_hits = _apply_patterns(text, INJECTION_PATTERNS, flags)
    extraction_score, extraction_hits = _apply_patterns(text, EXTRACTION_PATTERNS, flags)
    harmful_score, harmful_hits = _apply_patterns(text, HARMFUL_PATTERNS, flags)

    score += injection_score + extraction_score + harmful_score

    for terms, weight, label in SUSPICIOUS_TERM_COMBINATIONS:
        if all(term in text for term in terms):
            score += weight
            flags.append(label)

    keyword_hits = [keyword for keyword in HIGH_RISK_KEYWORDS if keyword in text]
    if keyword_hits:
        flags.extend([f"keyword::{hit}" for hit in keyword_hits])
        score = max(score, 0.92)

    if harmful_hits > 0:
        score = max(score, 0.84 + min(0.14, 0.04 * (harmful_hits - 1)))
    elif extraction_hits > 0 and injection_hits > 0:
        score = max(score, 0.72)
    elif extraction_hits > 0:
        score = max(score, 0.58 + min(0.08, 0.02 * (extraction_hits - 1)))
    elif injection_hits > 0:
        score = max(score, 0.46 + min(0.08, 0.02 * (injection_hits - 1)))

    if len(text) > 900:
        score += 0.04
        flags.append("very_long_prompt")

    if text.count("ignore") >= 2:
        score += 0.08
        flags.append("repeated_ignore_language")

    if text.count("reveal") >= 2:
        score += 0.06
        flags.append("repeated_reveal_language")

    score = _clamp(score)
    return round(score, 4), _dedupe(flags)


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

    if final_score >= 0.60:
        decision = GuardDecision.BLOCK
        reason = (
            "Prompt blocked due to high-risk abuse, prompt-injection, or secret-extraction indicators. "
            f"static_score={round(static_score, 4)}"
        )
    elif final_score >= 0.35:
        decision = GuardDecision.CHALLENGE
        reason = (
            "Prompt requires challenge due to moderate-risk indicators. "
            f"static_score={round(static_score, 4)}"
        )
    else:
        decision = GuardDecision.ALLOW
        reason = (
            "Prompt allowed with low-risk indicators. "
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

    if score >= 0.60:
        decision = "block"
        reason = "High-risk abuse / prompt-injection / secret extraction indicators detected."
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
