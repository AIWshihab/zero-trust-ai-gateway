from typing import Any

from app.core.model_trust_engine import compute_model_trust_score
from app.services.provider_inspector import inspect_provider
from app.services.infrastructure_assessor import assess_infrastructure
from app.services.behavioral_tester import run_behavioral_tests


async def scan_model(
    *,
    name: str,
    model_type: str | None,
    provider_name: str | None,
    source_url: str | None,
    hf_model_id: str | None,
    endpoint: str | None,
) -> dict[str, Any]:
    provider_data = await inspect_provider(
        provider_name=provider_name,
        source_url=source_url,
        hf_model_id=hf_model_id,
        endpoint=endpoint,
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
        "findings": trust_result.findings,
        "limitations": trust_result.limitations,
        "raw_inputs": {
            "provider_data": provider_data,
            "infrastructure_data": infrastructure_data,
            "behavioral_data": behavioral_data,
        },
    }