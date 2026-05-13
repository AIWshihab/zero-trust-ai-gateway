from datetime import datetime
from typing import Any

from app.core.config import get_settings
from app.core.model_trust_engine import compute_model_trust_score
from app.services.behavioral_tester import run_behavioral_tests
from app.services.infrastructure_assessor import assess_infrastructure
from app.services.model_posture_engine import build_control_context, compute_model_security_posture
from app.services.provider_inspector import inspect_provider


async def scan_model(
    *,
    name: str,
    model_type: str | None,
    provider_name: str | None,
    source_url: str | None,
    hf_model_id: str | None,
    endpoint: str | None,
    description: str | None = None,
    secure_mode_enabled: bool = False,
    protection_config: dict[str, Any] | None = None,
    previous_scan_at: datetime | None = None,
) -> dict[str, Any]:
    provider_data = await inspect_provider(
        provider_name=provider_name,
        source_url=source_url,
        hf_model_id=hf_model_id,
        endpoint=endpoint,
        description=description,
    )

    infrastructure_data = await assess_infrastructure(
        endpoint=endpoint,
        source_url=source_url,
    )

    behavioral_data = await run_behavioral_tests(
        model_type=model_type,
        endpoint=endpoint,
        provider_name=provider_name,
        hf_model_id=hf_model_id,
    )

    trust_result = compute_model_trust_score(
        provider_data=provider_data,
        infrastructure_data=infrastructure_data,
        behavioral_data=behavioral_data,
    )

    settings = get_settings()
    control_context = build_control_context(
        settings=settings,
        secure_mode_enabled=secure_mode_enabled,
        protection_config=protection_config,
    )

    posture_result = compute_model_security_posture(
        model_type=model_type,
        provider_name=provider_data.get("provider_name") or provider_name,
        source_url=source_url,
        endpoint=endpoint,
        provider_data=provider_data,
        infrastructure_data=infrastructure_data,
        behavioral_data=behavioral_data,
        previous_scan_at=previous_scan_at,
        control_context=control_context,
    )

    findings = list(trust_result.findings)
    findings.append(
        (
            f"Posture assessed at {posture_result['posture_assessed_at']} "
            f"with base risk {posture_result['base_risk_score']}/100 and "
            f"secured risk {posture_result['secured_risk_score']}/100."
        )
    )

    return {
        "model_name": name,
        "model_type": model_type,
        "provider_name": provider_data.get("provider_name") or provider_name,
        "base_trust_score": trust_result.base_trust_score,
        "breakdown": {
            "source_reputation": trust_result.breakdown.source_reputation,
            "metadata_completeness": trust_result.breakdown.metadata_completeness,
            "endpoint_security": trust_result.breakdown.endpoint_security,
            "behavioral_safety": trust_result.breakdown.behavioral_safety,
            "infrastructure_posture": trust_result.breakdown.infrastructure_posture,
        },
        "base_risk_score": posture_result["base_risk_score"],
        "secured_risk_score": posture_result["secured_risk_score"],
        "risk_reduction_pct": posture_result["risk_reduction_pct"],
        "posture_factors": posture_result["posture_factors"],
        "secured_risk_controls": posture_result["secured_risk_controls"],
        "posture_explanations": posture_result["posture_explanations"],
        "risk_reduction_explanations": posture_result["risk_reduction_explanations"],
        "posture_assessed_at": posture_result["posture_assessed_at"],
        "posture_expires_at": posture_result["posture_expires_at"],
        "scan_valid_until": posture_result["scan_valid_until"],
        "scan_freshness_days": posture_result["scan_freshness_days"],
        "findings": findings,
        "limitations": trust_result.limitations,
        "raw_inputs": {
            "provider_data": provider_data,
            "infrastructure_data": infrastructure_data,
            "behavioral_data": behavioral_data,
            "control_context": control_context,
        },
    }
