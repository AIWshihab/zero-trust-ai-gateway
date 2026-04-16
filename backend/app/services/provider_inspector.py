from typing import Any


def _normalize_provider(provider_name: str | None, source_url: str | None, endpoint: str | None) -> str:
    provider = (provider_name or "").strip()
    source = (source_url or "").lower()
    ep = (endpoint or "").lower()

    if provider:
        return provider

    if "huggingface.co" in source or "huggingface.co" in ep:
        return "HuggingFace"
    if "openai.com" in source or "openai.com" in ep:
        return "OpenAI"
    if "anthropic.com" in source or "anthropic.com" in ep:
        return "Anthropic"

    return "Unknown"


def _score_source_reputation(provider_name: str) -> tuple[float, list[str]]:
    findings: list[str] = []
    normalized = provider_name.lower()

    if normalized in {"openai", "huggingface", "anthropic"}:
        findings.append(f"Recognized provider: {provider_name}.")
        return 65.0, findings

    if normalized == "unknown":
        findings.append("Provider could not be confidently identified.")
        return 35.0, findings

    findings.append(f"Custom or less-known provider detected: {provider_name}.")
    return 45.0, findings


def _detect_license_status(
    *,
    source_url: str | None,
    hf_model_id: str | None,
    provider_name: str,
) -> str:
    """
    Returns one of: present, missing, unknown.
    """
    source = (source_url or "").lower()
    hf_id = (hf_model_id or "").lower()
    provider = provider_name.lower()

    explicit_license_markers = (
        "license",
        "licenses",
        "apache-2.0",
        "mit",
        "bsd",
        "cc-by",
    )

    if any(marker in source for marker in explicit_license_markers) or any(
        marker in hf_id for marker in explicit_license_markers
    ):
        return "present"

    if provider == "huggingface" and not hf_model_id:
        return "missing"

    # For managed providers and unknown external sources, treat as unknown
    # unless explicit metadata says otherwise.
    return "unknown"


def _score_metadata_completeness(
    *,
    source_url: str | None,
    endpoint: str | None,
    hf_model_id: str | None,
    provider_name: str,
    description: str | None,
) -> tuple[float, dict[str, Any], list[str]]:
    score = 10.0
    findings: list[str] = []

    has_source_url = bool(source_url)
    has_endpoint = bool(endpoint)
    has_hf_model_id = bool(hf_model_id)
    has_description = bool((description or "").strip())

    has_author = False
    has_model_card = False
    inferred_task = None

    license_status = _detect_license_status(
        source_url=source_url,
        hf_model_id=hf_model_id,
        provider_name=provider_name,
    )
    has_license = license_status == "present"

    if has_source_url:
        score += 20.0
    else:
        findings.append("Source URL not provided.")

    if has_endpoint:
        score += 20.0
    else:
        findings.append("Model/API endpoint not provided.")

    if provider_name.lower() == "huggingface":
        if has_hf_model_id:
            score += 20.0
            findings.append("Hugging Face model identifier provided.")
            has_model_card = True

            hf_id = hf_model_id.lower()
            if "gpt" in hf_id or "llama" in hf_id or "mistral" in hf_id or "qwen" in hf_id:
                inferred_task = "text-generation"
            elif "bert" in hf_id or "roberta" in hf_id:
                inferred_task = "fill-mask"
        else:
            findings.append("Hugging Face model identifier missing for Hugging Face provider.")

    if source_url and "huggingface.co/" in source_url.lower():
        has_model_card = True
        score += 10.0

    if provider_name.lower() in {"openai", "anthropic"}:
        score += 10.0
        has_author = True

    if "/models/" in (endpoint or "").lower():
        score += 5.0

    if provider_name.lower() == "huggingface" and hf_model_id:
        has_author = "/" in hf_model_id

    if has_description:
        score += 10.0
    else:
        findings.append("Model description missing.")

    if has_author:
        score += 5.0
    else:
        findings.append("Model author/owner could not be inferred.")

    if has_license:
        score += 10.0
    elif license_status == "missing":
        findings.append("License information appears missing.")
    else:
        findings.append("License information could not be verified.")

    score = min(score, 100.0)

    metadata = {
        "has_source_url": has_source_url,
        "has_endpoint": has_endpoint,
        "has_hf_model_id": has_hf_model_id,
        "has_license": has_license,
        "license_status": license_status,
        "has_description": has_description,
        "has_author": has_author,
        "has_model_card": has_model_card,
        "inferred_task": inferred_task,
    }

    return score, metadata, findings


async def inspect_provider(
    *,
    provider_name: str | None,
    source_url: str | None,
    hf_model_id: str | None,
    endpoint: str | None,
    description: str | None = None,
) -> dict[str, Any]:
    normalized_provider = _normalize_provider(provider_name, source_url, endpoint)

    source_reputation_score, source_findings = _score_source_reputation(normalized_provider)
    metadata_completeness_score, metadata, metadata_findings = _score_metadata_completeness(
        source_url=source_url,
        endpoint=endpoint,
        hf_model_id=hf_model_id,
        provider_name=normalized_provider,
        description=description,
    )

    findings = []
    findings.extend(source_findings)
    findings.extend(metadata_findings)

    return {
        "provider_name": normalized_provider,
        "source_reputation_score": round(source_reputation_score, 2),
        "metadata_completeness_score": round(metadata_completeness_score, 2),
        "has_source_url": metadata["has_source_url"],
        "has_endpoint": metadata["has_endpoint"],
        "has_hf_model_id": metadata["has_hf_model_id"],
        "has_license": metadata["has_license"],
        "license_status": metadata["license_status"],
        "has_description": metadata["has_description"],
        "has_author": metadata["has_author"],
        "has_model_card": metadata["has_model_card"],
        "inferred_task": metadata["inferred_task"],
        "findings": findings,
    }
