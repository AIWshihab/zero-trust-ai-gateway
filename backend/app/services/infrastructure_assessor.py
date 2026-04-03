from typing import Any
import time
from urllib.parse import urlparse

import httpx


def _safe_url(target: str | None) -> str | None:
    value = (target or "").strip()
    return value or None


def _basic_scheme_score(parsed_scheme: str) -> tuple[float, bool, list[str]]:
    findings: list[str] = []

    if parsed_scheme == "https":
        findings.append("HTTPS detected.")
        return 35.0, True, findings

    findings.append("HTTPS not detected or scheme missing.")
    return 5.0, False, findings


async def _probe_endpoint(endpoint: str) -> dict[str, Any]:
    findings: list[str] = []
    reachable = False
    auth_required = False
    status_code = None
    response_time_ms = None

    timeout = httpx.Timeout(connect=10.0, read=15.0, write=10.0, pool=10.0)

    try:
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
            start = time.perf_counter()
            resp = await client.get(endpoint)
            status_code = resp.status_code
            reachable = resp.status_code < 500
            response_time_ms = round((time.perf_counter() - start) * 1000, 2)

            if resp.status_code in {401, 403}:
                auth_required = True
                findings.append(f"Endpoint responded with {resp.status_code}, suggesting authentication or access control.")
            elif resp.status_code == 404:
                findings.append("Endpoint responded with 404 Not Found.")
            elif resp.status_code < 400:
                findings.append(f"Endpoint reachable with status {resp.status_code}.")
            else:
                findings.append(f"Endpoint responded with status {resp.status_code}.")

            server_header = resp.headers.get("server")
            if server_header:
                findings.append(f"Server header observed: {server_header}")

            cache_header = resp.headers.get("x-cache") or resp.headers.get("cf-cache-status")
            if cache_header:
                findings.append("Caching/CDN-related header observed.")

    except Exception as exc:
        findings.append(f"Endpoint probe failed: {exc}")

    return {
        "endpoint_reachable": reachable,
        "requires_auth": auth_required,
        "status_code": status_code,
        "response_time_ms": response_time_ms,
        "findings": findings,
    }


async def assess_infrastructure(
    *,
    endpoint: str | None,
    source_url: str | None,
) -> dict[str, Any]:
    findings: list[str] = []

    endpoint_security_score = 10.0
    infrastructure_posture_score = 10.0

    supports_https = False
    requires_auth = False
    endpoint_reachable = False

    target = _safe_url(endpoint) or _safe_url(source_url)
    if not target:
        findings.append("No endpoint or source URL available for infrastructure assessment.")
        return {
            "supports_https": False,
            "requires_auth": False,
            "endpoint_reachable": False,
            "endpoint_security_score": endpoint_security_score,
            "infrastructure_posture_score": infrastructure_posture_score,
            "findings": findings,
        }

    parsed = urlparse(target)

    scheme_score, supports_https, scheme_findings = _basic_scheme_score(parsed.scheme.lower())
    endpoint_security_score += scheme_score
    findings.extend(scheme_findings)

    if parsed.netloc:
        infrastructure_posture_score += 15.0
    else:
        findings.append("Endpoint host could not be parsed clearly.")

    if endpoint:
        infrastructure_posture_score += 10.0
        findings.append("Endpoint provided for runtime access.")

        probe_result = await _probe_endpoint(endpoint)
        endpoint_reachable = bool(probe_result["endpoint_reachable"])
        requires_auth = bool(probe_result["requires_auth"])
        findings.extend(probe_result["findings"])

        if endpoint_reachable:
            infrastructure_posture_score += 20.0
        if requires_auth:
            endpoint_security_score += 20.0
        else:
            findings.append("No clear authentication requirement observed from supplied details.")
    else:
        findings.append("No direct endpoint provided; only source URL was available.")

    if supports_https and endpoint_reachable:
        endpoint_security_score += 10.0

    endpoint_security_score = min(endpoint_security_score, 100.0)
    infrastructure_posture_score = min(infrastructure_posture_score, 100.0)

    return {
        "supports_https": supports_https,
        "requires_auth": requires_auth,
        "endpoint_reachable": endpoint_reachable,
        "endpoint_security_score": round(endpoint_security_score, 2),
        "infrastructure_posture_score": round(infrastructure_posture_score, 2),
        "findings": findings,
    }
