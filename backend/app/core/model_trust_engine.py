from dataclasses import dataclass, field
from typing import Any


@dataclass
class TrustBreakdown:
    source_reputation: float = 0.0
    metadata_completeness: float = 0.0
    endpoint_security: float = 0.0
    behavioral_safety: float = 0.0
    infrastructure_posture: float = 0.0


@dataclass
class TrustAssessmentResult:
    base_trust_score: float
    breakdown: TrustBreakdown
    findings: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)
    raw_inputs: dict[str, Any] = field(default_factory=dict)


def _clamp_score(value: float) -> float:
    return max(0.0, min(100.0, value))


def compute_model_trust_score(
    provider_data: dict[str, Any],
    infrastructure_data: dict[str, Any],
    behavioral_data: dict[str, Any],
) -> TrustAssessmentResult:
    breakdown = TrustBreakdown(
        source_reputation=float(provider_data.get("source_reputation_score", 0.0)),
        metadata_completeness=float(provider_data.get("metadata_completeness_score", 0.0)),
        endpoint_security=float(infrastructure_data.get("endpoint_security_score", 0.0)),
        behavioral_safety=float(behavioral_data.get("behavioral_safety_score", 0.0)),
        infrastructure_posture=float(infrastructure_data.get("infrastructure_posture_score", 0.0)),
    )

    weighted_score = (
        breakdown.source_reputation * 0.20
        + breakdown.metadata_completeness * 0.20
        + breakdown.endpoint_security * 0.20
        + breakdown.behavioral_safety * 0.25
        + breakdown.infrastructure_posture * 0.15
    )

    findings: list[str] = []
    findings.extend(provider_data.get("findings", []))
    findings.extend(infrastructure_data.get("findings", []))
    findings.extend(behavioral_data.get("findings", []))

    limitations = [
        "Assessment is based on observable metadata, endpoint behavior, and accessible signals only.",
        "Internal provider infrastructure and hidden model internals may not be fully visible.",
    ]

    if not provider_data.get("has_model_card", False):
        limitations.append("Model card completeness could not be fully verified.")
    if not infrastructure_data.get("endpoint_reachable", False):
        limitations.append("Runtime endpoint reachability was limited or unavailable during assessment.")

    return TrustAssessmentResult(
        base_trust_score=round(_clamp_score(weighted_score), 2),
        breakdown=breakdown,
        findings=findings,
        limitations=limitations,
        raw_inputs={
            "provider_data": provider_data,
            "infrastructure_data": infrastructure_data,
            "behavioral_data": behavioral_data,
        },
    )