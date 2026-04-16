from datetime import datetime, timedelta, timezone
import ipaddress
from typing import Any
from urllib.parse import urlparse


SCAN_VALIDITY_DAYS = 30
MAX_TOTAL_REDUCTION_RATIO = 0.45

FACTOR_WEIGHTS: dict[str, float] = {
    "provider_reputation": 0.15,
    "source_type": 0.10,
    "metadata_completeness": 0.15,
    "license_presence": 0.15,
    "endpoint_security": 0.15,
    "safety_information_availability": 0.15,
    "exposure_hosting_posture": 0.10,
    "scan_freshness": 0.05,
}

CONTROL_REDUCTION_RATIOS: dict[str, float] = {
    "gateway_authenticated_access": 0.02,
    "prompt_guard_filtering": 0.04,
    "policy_engine_enforcement": 0.04,
    "adaptive_trust_decisions": 0.03,
    "rate_limiting_abuse_controls": 0.03,
    "monitoring_audit_logging": 0.02,
    "secure_mode_enforcement": 0.12,
    "output_guard_filtering": 0.10,
}

CONTROL_DESCRIPTIONS: dict[str, str] = {
    "gateway_authenticated_access": "Authenticated gateway-only model access",
    "prompt_guard_filtering": "Prompt guard filtering and abuse detection",
    "policy_engine_enforcement": "Central policy engine decisioning",
    "adaptive_trust_decisions": "User trust-aware policy penalties",
    "rate_limiting_abuse_controls": "Rate limiting and burst-abuse safeguards",
    "monitoring_audit_logging": "Monitoring, logging, and audit trail",
    "secure_mode_enforcement": "Secure mode enforcement for stricter protections",
    "output_guard_filtering": "Output guard redaction/block enforcement",
}

DEFAULT_CONTROL_CONTEXT: dict[str, bool] = {
    "gateway_authenticated_access": True,
    "prompt_guard_filtering": True,
    "policy_engine_enforcement": True,
    "adaptive_trust_decisions": True,
    "rate_limiting_abuse_controls": True,
    "monitoring_audit_logging": True,
    "secure_mode_enforcement": False,
    "output_guard_filtering": False,
}


def _clamp_100(value: float) -> float:
    return max(0.0, min(100.0, float(value)))


def _to_float(value: Any, default: float) -> float:
    try:
        return float(value)
    except Exception:
        return float(default)


def _extract_host(url: str | None) -> str:
    raw = (url or "").strip()
    if not raw:
        return ""
    parsed = urlparse(raw)
    return (parsed.hostname or "").lower()


def _is_private_or_local_host(host: str) -> bool:
    if not host:
        return False
    if host in {"localhost", "127.0.0.1", "::1"}:
        return True
    if host.endswith(".local") or host.endswith(".internal"):
        return True

    try:
        ip = ipaddress.ip_address(host)
        return bool(ip.is_private or ip.is_loopback)
    except Exception:
        return False


def _factor_payload(
    *,
    score: float,
    weight: float,
    reason: str,
    signals: dict[str, Any],
) -> dict[str, Any]:
    posture_score = round(_clamp_100(score), 2)
    risk_score = round(100.0 - posture_score, 2)
    return {
        "posture_score": posture_score,
        "risk_score": risk_score,
        "weight": weight,
        "weighted_posture_contribution": round(posture_score * weight, 2),
        "reason": reason,
        "signals": signals,
    }


def _provider_reputation_factor(provider_data: dict[str, Any]) -> tuple[float, str, dict[str, Any]]:
    score = _clamp_100(_to_float(provider_data.get("source_reputation_score"), 40.0))
    provider_name = str(provider_data.get("provider_name") or "unknown")

    if score >= 60:
        reason = f"Provider reputation is relatively strong ({score:.1f}/100)."
    elif score >= 45:
        reason = f"Provider reputation is moderate ({score:.1f}/100)."
    else:
        reason = f"Provider reputation is weak or uncertain ({score:.1f}/100)."

    return score, reason, {"provider_name": provider_name}


def _source_type_factor(
    *,
    model_type: str | None,
    source_url: str | None,
    endpoint: str | None,
    provider_name: str | None,
) -> tuple[float, str, dict[str, Any]]:
    model_type_norm = (model_type or "").lower()
    provider_norm = (provider_name or "").lower()
    source_host = _extract_host(source_url)
    endpoint_host = _extract_host(endpoint)

    known_hosts = {"huggingface.co", "api.openai.com", "api.anthropic.com"}

    if model_type_norm == "local" or _is_private_or_local_host(endpoint_host):
        score = 85.0
        reason = "Model source appears local/private, reducing exposure from unknown public hosts."
    elif source_host in known_hosts or provider_norm in {"openai", "huggingface", "anthropic"}:
        score = 72.0
        reason = "Model source appears to be a recognized managed/known provider host."
    elif endpoint_host:
        score = 45.0
        reason = "Model is served from a public custom endpoint with limited source assurances."
    elif source_host:
        score = 55.0
        reason = "Model source URL is present but provider/source type assurance is limited."
    else:
        score = 25.0
        reason = "Model source type is unclear due to missing source and endpoint metadata."

    return score, reason, {
        "model_type": model_type_norm or None,
        "provider_name": provider_norm or None,
        "source_host": source_host or None,
        "endpoint_host": endpoint_host or None,
    }


def _metadata_completeness_factor(provider_data: dict[str, Any]) -> tuple[float, str, dict[str, Any]]:
    score = _clamp_100(_to_float(provider_data.get("metadata_completeness_score"), 35.0))

    has_source_url = bool(provider_data.get("has_source_url"))
    has_endpoint = bool(provider_data.get("has_endpoint"))
    has_hf_model_id = bool(provider_data.get("has_hf_model_id"))
    has_description = bool(provider_data.get("has_description"))
    has_author = bool(provider_data.get("has_author"))
    license_status = str(provider_data.get("license_status") or "unknown").lower()

    if not has_description:
        score -= 8.0
    if not has_author:
        score -= 6.0
    if not has_source_url and not has_endpoint:
        score -= 10.0
    if license_status != "present":
        score -= 10.0
    if has_hf_model_id:
        score += 3.0

    score = _clamp_100(score)

    missing_bits = []
    if not has_source_url:
        missing_bits.append("source_url")
    if not has_endpoint:
        missing_bits.append("endpoint")
    if not has_description:
        missing_bits.append("description")
    if not has_author:
        missing_bits.append("author")
    if license_status != "present":
        missing_bits.append("license")

    if missing_bits:
        reason = "Metadata completeness is reduced due to missing: " + ", ".join(missing_bits) + "."
    else:
        reason = "Metadata completeness appears strong across key fields."

    return score, reason, {
        "has_source_url": has_source_url,
        "has_endpoint": has_endpoint,
        "has_hf_model_id": has_hf_model_id,
        "has_description": has_description,
        "has_author": has_author,
        "license_status": license_status,
    }


def _license_presence_factor(provider_data: dict[str, Any]) -> tuple[float, str, dict[str, Any]]:
    license_status = str(provider_data.get("license_status") or "unknown").lower()
    has_license = bool(provider_data.get("has_license"))

    if has_license or license_status == "present":
        score = 90.0
        reason = "License information is explicitly present."
    elif license_status == "missing":
        score = 20.0
        reason = "License information appears missing, increasing compliance and usage risk."
    else:
        score = 30.0
        reason = "License information is unknown and treated as elevated risk by default."

    return score, reason, {
        "license_status": license_status,
        "has_license": has_license,
    }


def _endpoint_security_factor(infrastructure_data: dict[str, Any]) -> tuple[float, str, dict[str, Any]]:
    score = _clamp_100(_to_float(infrastructure_data.get("endpoint_security_score"), 25.0))

    supports_https = bool(infrastructure_data.get("supports_https"))
    requires_auth = bool(infrastructure_data.get("requires_auth"))
    endpoint_reachable = bool(infrastructure_data.get("endpoint_reachable"))

    if not supports_https:
        score -= 12.0
    if not requires_auth:
        score -= 15.0
    if not endpoint_reachable:
        score -= 5.0

    score = _clamp_100(score)

    reason_bits = []
    reason_bits.append("HTTPS" if supports_https else "no HTTPS")
    reason_bits.append("auth required" if requires_auth else "no clear auth")
    reason_bits.append("reachable" if endpoint_reachable else "unreachable/uncertain")
    reason = "Endpoint security reflects: " + ", ".join(reason_bits) + "."

    return score, reason, {
        "supports_https": supports_https,
        "requires_auth": requires_auth,
        "endpoint_reachable": endpoint_reachable,
    }


def _safety_info_factor(
    provider_data: dict[str, Any],
    behavioral_data: dict[str, Any],
) -> tuple[float, str, dict[str, Any]]:
    has_model_card = bool(provider_data.get("has_model_card"))
    has_description = bool(provider_data.get("has_description"))

    tests_run = behavioral_data.get("tests_run") or []
    passed_tests = int(_to_float(behavioral_data.get("passed_tests"), 0.0))
    failed_tests = int(_to_float(behavioral_data.get("failed_tests"), 0.0))

    score = 15.0
    if has_model_card:
        score += 45.0
    if has_description:
        score += 15.0

    if tests_run:
        score += 10.0
        if failed_tests == 0 and passed_tests > 0:
            score += 20.0
        elif failed_tests > 0:
            score -= min(25.0, failed_tests * 8.0)
    else:
        score -= 5.0

    score = _clamp_100(score)

    if score >= 70:
        reason = "Safety information is reasonably available from model metadata and behavioral checks."
    elif score >= 45:
        reason = "Safety information is partial; additional evidence is recommended."
    else:
        reason = "Safety information is weak or missing, increasing uncertainty risk."

    return score, reason, {
        "has_model_card": has_model_card,
        "has_description": has_description,
        "tests_run_count": len(tests_run),
        "passed_tests": passed_tests,
        "failed_tests": failed_tests,
    }


def _exposure_hosting_factor(
    *,
    endpoint: str | None,
    source_url: str | None,
    infrastructure_data: dict[str, Any],
) -> tuple[float, str, dict[str, Any]]:
    endpoint_host = _extract_host(endpoint)
    source_host = _extract_host(source_url)

    supports_https = bool(infrastructure_data.get("supports_https"))
    requires_auth = bool(infrastructure_data.get("requires_auth"))
    endpoint_reachable = bool(infrastructure_data.get("endpoint_reachable"))

    if endpoint_host:
        score = 50.0
        score += 15.0 if supports_https else -20.0
        score += 20.0 if requires_auth else -20.0
        score += 10.0 if _is_private_or_local_host(endpoint_host) else -10.0
        score += 5.0 if not endpoint_reachable else 0.0
    elif source_host:
        score = 40.0
        if source_host in {"huggingface.co", "api.openai.com", "api.anthropic.com"}:
            score += 10.0
    else:
        score = 25.0

    score = _clamp_100(score)

    if score >= 70:
        reason = "Hosting exposure posture is relatively controlled."
    elif score >= 45:
        reason = "Hosting exposure posture is moderate with some uncertainty."
    else:
        reason = "Hosting exposure posture is high risk due to public/weakly controlled access patterns."

    return score, reason, {
        "endpoint_host": endpoint_host or None,
        "source_host": source_host or None,
        "supports_https": supports_https,
        "requires_auth": requires_auth,
        "endpoint_reachable": endpoint_reachable,
        "private_or_local_endpoint": _is_private_or_local_host(endpoint_host),
    }


def _scan_freshness_factor(
    *,
    assessed_at: datetime,
    previous_scan_at: datetime | None,
) -> tuple[float, int, str, dict[str, Any]]:
    reference = previous_scan_at or assessed_at
    days_old = max(0, int((assessed_at - reference).total_seconds() // 86400))

    if days_old <= 1:
        score = 100.0
    elif days_old <= 7:
        score = 90.0
    elif days_old <= 30:
        score = 75.0
    elif days_old <= 60:
        score = 55.0
    elif days_old <= 90:
        score = 40.0
    else:
        score = 25.0

    reason = f"Scan freshness is {days_old} day(s) old at assessment time."
    return score, days_old, reason, {"days_old": days_old}


def _compute_secured_risk(
    *,
    base_risk_score: float,
    control_context: dict[str, bool] | None,
) -> tuple[float, float, dict[str, Any], list[str]]:
    context = control_context or {}

    controls: list[dict[str, Any]] = []
    raw_reduction_ratio = 0.0

    for control_key, control_ratio in CONTROL_REDUCTION_RATIOS.items():
        active = bool(context.get(control_key, False))
        potential_ratio = control_ratio if active else 0.0
        raw_reduction_ratio += potential_ratio

        controls.append(
            {
                "control_key": control_key,
                "control_name": CONTROL_DESCRIPTIONS[control_key],
                "active": active,
                "potential_reduction_ratio": round(potential_ratio, 4),
                "applied_reduction_ratio": 0.0,
                "applied_reduction_points": 0.0,
                "description": CONTROL_DESCRIPTIONS[control_key],
            }
        )

    bounded_reduction_ratio = min(raw_reduction_ratio, MAX_TOTAL_REDUCTION_RATIO)
    scale = (bounded_reduction_ratio / raw_reduction_ratio) if raw_reduction_ratio > 0 else 0.0

    total_reduction_points = base_risk_score * bounded_reduction_ratio
    secured_risk_score = _clamp_100(base_risk_score - total_reduction_points)

    risk_reduction_pct = 0.0
    if base_risk_score > 0:
        risk_reduction_pct = ((base_risk_score - secured_risk_score) / base_risk_score) * 100.0

    explanations: list[str] = []
    if bounded_reduction_ratio <= 0:
        explanations.append("No active protections qualified for risk reduction under current configuration.")
    else:
        explanations.append(
            (
                f"Secured risk is reduced by {round(risk_reduction_pct, 2)}% "
                f"from base risk using explicit gateway protections "
                f"(bounded reduction ratio {round(bounded_reduction_ratio, 4)})."
            )
        )

    for control in controls:
        if not control["active"]:
            continue
        applied_ratio = control["potential_reduction_ratio"] * scale
        applied_points = base_risk_score * applied_ratio

        control["applied_reduction_ratio"] = round(applied_ratio, 4)
        control["applied_reduction_points"] = round(applied_points, 2)

        explanations.append(
            (
                f"{control['control_name']} lowered risk by {round(applied_points, 2)} points "
                f"({round(applied_ratio * 100, 2)}% of base risk)."
            )
        )

    controls_summary = {
        "method": "bounded_additive_control_reduction",
        "max_total_reduction_ratio": MAX_TOTAL_REDUCTION_RATIO,
        "raw_reduction_ratio": round(raw_reduction_ratio, 4),
        "bounded_reduction_ratio": round(bounded_reduction_ratio, 4),
        "controls": controls,
    }

    return round(secured_risk_score, 2), round(risk_reduction_pct, 2), controls_summary, explanations


def build_control_context(
    *,
    settings,
    secure_mode_enabled: bool,
    protection_config: dict[str, Any] | None = None,
) -> dict[str, bool]:
    cfg = protection_config or {}

    return {
        "gateway_authenticated_access": bool(cfg.get("require_auth", DEFAULT_CONTROL_CONTEXT["gateway_authenticated_access"])),
        "prompt_guard_filtering": bool(settings.PROMPT_ANALYSIS_ENABLED) and bool(
            cfg.get("prompt_filtering", DEFAULT_CONTROL_CONTEXT["prompt_guard_filtering"])
        ),
        "policy_engine_enforcement": bool(settings.ZTA_ENABLED) and bool(
            cfg.get("policy_engine_enforcement", DEFAULT_CONTROL_CONTEXT["policy_engine_enforcement"])
        ),
        "adaptive_trust_decisions": bool(settings.USER_TRUST_SCORE_ENABLED) and bool(
            cfg.get("adaptive_trust_decisions", DEFAULT_CONTROL_CONTEXT["adaptive_trust_decisions"])
        ),
        "rate_limiting_abuse_controls": bool(settings.RATE_LIMITING_ENABLED) and bool(
            cfg.get("rate_limit_enabled", DEFAULT_CONTROL_CONTEXT["rate_limiting_abuse_controls"])
        ),
        "monitoring_audit_logging": bool(cfg.get("logging_enabled", DEFAULT_CONTROL_CONTEXT["monitoring_audit_logging"])),
        "secure_mode_enforcement": bool(secure_mode_enabled),
        "output_guard_filtering": bool(secure_mode_enabled) and bool(cfg.get("output_filtering", True)),
    }


def compute_secured_risk_from_controls(
    *,
    base_risk_score: float,
    control_context: dict[str, bool] | None,
) -> dict[str, Any]:
    secured_risk_score, risk_reduction_pct, secured_risk_controls, risk_reduction_explanations = _compute_secured_risk(
        base_risk_score=_clamp_100(base_risk_score),
        control_context=control_context,
    )

    return {
        "secured_risk_score": secured_risk_score,
        "risk_reduction_pct": risk_reduction_pct,
        "secured_risk_controls": secured_risk_controls,
        "risk_reduction_explanations": risk_reduction_explanations,
    }


def compute_model_security_posture(
    *,
    model_type: str | None,
    provider_name: str | None,
    source_url: str | None,
    endpoint: str | None,
    provider_data: dict[str, Any],
    infrastructure_data: dict[str, Any],
    behavioral_data: dict[str, Any],
    previous_scan_at: datetime | None = None,
    control_context: dict[str, bool] | None = None,
) -> dict[str, Any]:
    assessed_at = datetime.now(timezone.utc)

    provider_score, provider_reason, provider_signals = _provider_reputation_factor(provider_data)
    source_type_score, source_type_reason, source_type_signals = _source_type_factor(
        model_type=model_type,
        source_url=source_url,
        endpoint=endpoint,
        provider_name=provider_name,
    )
    metadata_score, metadata_reason, metadata_signals = _metadata_completeness_factor(provider_data)
    license_score, license_reason, license_signals = _license_presence_factor(provider_data)
    endpoint_score, endpoint_reason, endpoint_signals = _endpoint_security_factor(infrastructure_data)
    safety_score, safety_reason, safety_signals = _safety_info_factor(provider_data, behavioral_data)
    exposure_score, exposure_reason, exposure_signals = _exposure_hosting_factor(
        endpoint=endpoint,
        source_url=source_url,
        infrastructure_data=infrastructure_data,
    )
    freshness_score, scan_freshness_days, freshness_reason, freshness_signals = _scan_freshness_factor(
        assessed_at=assessed_at,
        previous_scan_at=previous_scan_at,
    )

    factors = {
        "provider_reputation": _factor_payload(
            score=provider_score,
            weight=FACTOR_WEIGHTS["provider_reputation"],
            reason=provider_reason,
            signals=provider_signals,
        ),
        "source_type": _factor_payload(
            score=source_type_score,
            weight=FACTOR_WEIGHTS["source_type"],
            reason=source_type_reason,
            signals=source_type_signals,
        ),
        "metadata_completeness": _factor_payload(
            score=metadata_score,
            weight=FACTOR_WEIGHTS["metadata_completeness"],
            reason=metadata_reason,
            signals=metadata_signals,
        ),
        "license_presence": _factor_payload(
            score=license_score,
            weight=FACTOR_WEIGHTS["license_presence"],
            reason=license_reason,
            signals=license_signals,
        ),
        "endpoint_security": _factor_payload(
            score=endpoint_score,
            weight=FACTOR_WEIGHTS["endpoint_security"],
            reason=endpoint_reason,
            signals=endpoint_signals,
        ),
        "safety_information_availability": _factor_payload(
            score=safety_score,
            weight=FACTOR_WEIGHTS["safety_information_availability"],
            reason=safety_reason,
            signals=safety_signals,
        ),
        "exposure_hosting_posture": _factor_payload(
            score=exposure_score,
            weight=FACTOR_WEIGHTS["exposure_hosting_posture"],
            reason=exposure_reason,
            signals=exposure_signals,
        ),
        "scan_freshness": _factor_payload(
            score=freshness_score,
            weight=FACTOR_WEIGHTS["scan_freshness"],
            reason=freshness_reason,
            signals=freshness_signals,
        ),
    }

    posture_score = 0.0
    for factor_name, factor_data in factors.items():
        posture_score += factor_data["posture_score"] * FACTOR_WEIGHTS[factor_name]

    posture_score = round(_clamp_100(posture_score), 2)
    base_risk_score = round(100.0 - posture_score, 2)

    secured_risk_score, risk_reduction_pct, secured_risk_controls, risk_reduction_explanations = _compute_secured_risk(
        base_risk_score=base_risk_score,
        control_context=control_context,
    )

    explanations: list[str] = [
        (
            f"Model posture score {posture_score}/100 results in base risk {base_risk_score}/100. "
            "Missing or weak security signals increase risk by design."
        )
    ]

    ordered_factors = [
        "provider_reputation",
        "source_type",
        "metadata_completeness",
        "license_presence",
        "endpoint_security",
        "safety_information_availability",
        "exposure_hosting_posture",
        "scan_freshness",
    ]

    for factor_name in ordered_factors:
        factor = factors[factor_name]
        if factor["posture_score"] < 50:
            explanations.append(
                f"Risk driver: {factor_name.replace('_', ' ')} scored {factor['posture_score']}/100. {factor['reason']}"
            )

    explanations.extend(risk_reduction_explanations)

    if len(explanations) == 1:
        explanations.append("No major low-score posture factors were detected in this scan.")

    scan_valid_until = assessed_at + timedelta(days=SCAN_VALIDITY_DAYS)

    return {
        "posture_score": posture_score,
        "base_risk_score": base_risk_score,
        "secured_risk_score": secured_risk_score,
        "risk_reduction_pct": risk_reduction_pct,
        "posture_factors": factors,
        "secured_risk_controls": secured_risk_controls,
        "posture_explanations": explanations,
        "risk_reduction_explanations": risk_reduction_explanations,
        "posture_assessed_at": assessed_at.isoformat(),
        "posture_expires_at": scan_valid_until.isoformat(),
        "scan_valid_until": scan_valid_until.isoformat(),
        "scan_freshness_days": scan_freshness_days,
    }
