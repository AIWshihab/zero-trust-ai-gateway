import re
from typing import TypedDict

# ─── Threat Pattern Definitions ───────────────────────────────────────────────

INJECTION_PATTERNS = [
    r"ignore previous instructions",
    r"ignore all instructions",
    r"disregard (your|all|previous) (instructions|rules|guidelines)",
    r"you are now (a|an|the)",
    r"act as (a|an|the)",
    r"pretend (you are|to be)",
    r"jailbreak",
    r"do anything now",
    r"dan mode",
    r"override (safety|guidelines|rules)",
]

EXTRACTION_PATTERNS = [
    r"repeat (your|the) (system|training|instructions|prompt)",
    r"what (is|are) your (instructions|system prompt|training data)",
    r"show me your (prompt|instructions|system message)",
    r"reveal (your|the) (weights|parameters|training)",
    r"print (your|the) (system|initial) (prompt|instructions)",
    r"tell me (everything|all) you know about yourself",
]

HARMFUL_PATTERNS = [
    r"how to (make|build|create|synthesize) (a bomb|explosives|weapons|drugs|malware)",
    r"(generate|write|create) (malware|ransomware|virus|exploit)",
    r"(child|minor).{0,20}(explicit|sexual|nude)",
    r"(hack|crack|bypass).{0,20}(password|authentication|security)",
    r"(suicide|self.harm).{0,20}(method|how|way)",
]

# ─── Risk Weight Per Category ─────────────────────────────────────────────────

CATEGORY_WEIGHTS = {
    "injection":  0.85,
    "extraction": 0.90,
    "harmful":    1.00,
}

# ─── Types ────────────────────────────────────────────────────────────────────

class PromptAnalysisResult(TypedDict):
    risk_score: float
    flags: list[str]
    is_safe: bool


# ─── Core Analyser ────────────────────────────────────────────────────────────

def analyse_prompt(prompt: str) -> PromptAnalysisResult:
    """
    Scans a prompt for known threat patterns.
    Returns a normalised risk score [0.0 - 1.0] and list of flags.
    """
    prompt_lower = prompt.lower().strip()
    flags        = []
    max_score    = 0.0

    # Check injection patterns
    for pattern in INJECTION_PATTERNS:
        if re.search(pattern, prompt_lower):
            flags.append(f"INJECTION: {pattern}")
            max_score = max(max_score, CATEGORY_WEIGHTS["injection"])

    # Check extraction patterns
    for pattern in EXTRACTION_PATTERNS:
        if re.search(pattern, prompt_lower):
            flags.append(f"EXTRACTION: {pattern}")
            max_score = max(max_score, CATEGORY_WEIGHTS["extraction"])

    # Check harmful patterns
    for pattern in HARMFUL_PATTERNS:
        if re.search(pattern, prompt_lower):
            flags.append(f"HARMFUL: {pattern}")
            max_score = max(max_score, CATEGORY_WEIGHTS["harmful"])

    # Apply length heuristic — very long prompts slightly elevate risk
    length_penalty = min(len(prompt) / 10000, 0.15)
    final_score    = round(min(max_score + length_penalty, 1.0), 4)

    return PromptAnalysisResult(
        risk_score=final_score,
        flags=flags,
        is_safe=final_score < 0.5,
    )


# ─── Batch Screening ──────────────────────────────────────────────────────────

def screen_prompts(prompts: list[str]) -> list[PromptAnalysisResult]:
    """
    Screens multiple prompts at once.
    Used for bulk evaluation in experiments.
    """
    return [analyse_prompt(p) for p in prompts]


# ─── Quick Safety Check ───────────────────────────────────────────────────────

def is_safe_prompt(prompt: str) -> bool:
    return analyse_prompt(prompt)["is_safe"]
