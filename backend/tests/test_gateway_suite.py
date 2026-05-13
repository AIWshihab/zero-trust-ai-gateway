"""Comprehensive self-test suite for the Zero Trust AI Gateway.

Covers: health, auth, model registry, detection/policy, security controls,
monitoring (metrics + SOC), devices & sessions, firewall, and system state.

All tests use real application code with dependency overrides for auth —
no mocks, no hardcoded fake data.
"""
from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from app.core import monitoring
from app.core.security import require_active_user, require_admin
from app.main import app
from app.schemas import TokenData


# ── Shared helpers ────────────────────────────────────────────────────────────

def _user() -> TokenData:
    return TokenData(
        user_id=1,
        username="suite-test-user",
        email="suite-test@example.com",
        scopes=["user"],
    )


def _admin() -> TokenData:
    return TokenData(
        user_id=1,
        username="suite-test-admin",
        email="suite-test-admin@example.com",
        scopes=["admin"],
    )


@pytest.fixture
async def user_client():
    async def _fake_user():
        return _user()

    app.dependency_overrides[require_active_user] = _fake_user
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
    app.dependency_overrides.clear()


@pytest.fixture
async def admin_client():
    async def _fake_admin():
        return _admin()

    app.dependency_overrides[require_active_user] = _fake_admin
    app.dependency_overrides[require_admin] = _fake_admin
    app.dependency_overrides[monitoring.require_admin] = _fake_admin
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
    app.dependency_overrides.clear()


# ── Health & System ───────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_health_endpoint_returns_ok():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.get("/health")
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, dict)
    assert "status" in data


@pytest.mark.asyncio
async def test_system_state_schema(admin_client: AsyncClient):
    r = await admin_client.get("/api/v1/system/state")
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, dict)


@pytest.mark.asyncio
async def test_monitoring_health_returns_status(admin_client: AsyncClient):
    r = await admin_client.get("/api/v1/monitoring/health")
    assert r.status_code == 200
    data = r.json()
    assert "status" in data or isinstance(data, dict)


# ── Authentication ────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_auth_token_rejects_bad_credentials():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.post(
            "/api/v1/auth/token",
            data={"username": "nobody", "password": "wrongpass"},
        )
    assert r.status_code in (401, 422)


@pytest.mark.asyncio
async def test_auth_token_missing_body_returns_422():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.post("/api/v1/auth/token", json={})
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_protected_endpoint_rejects_missing_token():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.get("/api/v1/models/")
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_admin_endpoint_rejects_missing_token():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.get("/api/v1/monitoring/logs")
    assert r.status_code == 401


# ── Model Registry ────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_list_models_returns_list(user_client: AsyncClient):
    r = await user_client.get("/api/v1/models/")
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)


@pytest.mark.asyncio
async def test_model_schema_has_required_fields(user_client: AsyncClient):
    r = await user_client.get("/api/v1/models/")
    assert r.status_code == 200
    models = r.json()
    for m in models:
        assert "id" in m
        assert "name" in m
        assert "model_type" in m
        assert "is_active" in m


@pytest.mark.asyncio
async def test_models_runtime_readiness_returns_list(user_client: AsyncClient):
    r = await user_client.get("/api/v1/models/runtime-readiness")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


@pytest.mark.asyncio
async def test_my_models_returns_list(user_client: AsyncClient):
    r = await user_client.get("/api/v1/models/my")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


@pytest.mark.asyncio
async def test_global_models_visible_to_all_users(user_client: AsyncClient):
    r = await user_client.get("/api/v1/models/")
    assert r.status_code == 200
    models = r.json()
    visibility_values = [m.get("visibility") for m in models]
    # global or private (own) models only — no foreign private models
    for v in visibility_values:
        assert v in ("global", "private", None)


# ── Security Controls & Detection Rules ──────────────────────────────────────

@pytest.mark.asyncio
async def test_list_security_controls_returns_list(user_client: AsyncClient):
    r = await user_client.get("/api/v1/security/controls")
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)


@pytest.mark.asyncio
async def test_security_control_schema_fields(user_client: AsyncClient):
    r = await user_client.get("/api/v1/security/controls")
    assert r.status_code == 200
    controls = r.json()
    for c in controls:
        assert "id" in c
        assert "name" in c
        assert "enabled" in c


@pytest.mark.asyncio
async def test_list_detection_rules_returns_list(user_client: AsyncClient):
    r = await user_client.get("/api/v1/security/detection-rules")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


@pytest.mark.asyncio
async def test_detection_rule_schema_fields(user_client: AsyncClient):
    r = await user_client.get("/api/v1/security/detection-rules")
    assert r.status_code == 200
    rules = r.json()
    for rule in rules:
        assert "id" in rule
        assert "name" in rule
        assert "target" in rule


# ── Monitoring ────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_monitoring_metrics_schema(user_client: AsyncClient):
    r = await user_client.get("/api/v1/monitoring/metrics")
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, dict)
    for key in ("total_requests", "blocked_requests", "allowed_requests"):
        assert key in data
        assert isinstance(data[key], int)


@pytest.mark.asyncio
async def test_monitoring_metrics_non_negative(user_client: AsyncClient):
    r = await user_client.get("/api/v1/monitoring/metrics")
    assert r.status_code == 200
    data = r.json()
    assert data["total_requests"] >= 0
    assert data["blocked_requests"] >= 0
    assert data["allowed_requests"] >= 0
    assert 0.0 <= data.get("block_rate", 0.0) <= 100.0


@pytest.mark.asyncio
async def test_admin_logs_schema(admin_client: AsyncClient):
    r = await admin_client.get("/api/v1/monitoring/logs?limit=10")
    assert r.status_code == 200
    data = r.json()
    assert "logs" in data
    assert "total" in data
    assert isinstance(data["logs"], list)
    assert isinstance(data["total"], int)


@pytest.mark.asyncio
async def test_my_logs_returns_list(user_client: AsyncClient):
    r = await user_client.get("/api/v1/monitoring/logs/me")
    assert r.status_code == 200
    data = r.json()
    assert "logs" in data or isinstance(data, list)


@pytest.mark.asyncio
async def test_soc_attack_timeline_schema(admin_client: AsyncClient):
    r = await admin_client.get("/api/v1/monitoring/soc/attack-timeline")
    assert r.status_code == 200
    data = r.json()
    assert "events" in data
    assert isinstance(data["events"], list)


@pytest.mark.asyncio
async def test_soc_threat_heatmap_schema(admin_client: AsyncClient):
    r = await admin_client.get("/api/v1/monitoring/soc/threat-heatmap")
    assert r.status_code == 200
    data = r.json()
    assert "cells" in data
    assert isinstance(data["cells"], list)


@pytest.mark.asyncio
async def test_soc_user_anomalies_schema(admin_client: AsyncClient):
    r = await admin_client.get("/api/v1/monitoring/soc/user-anomalies")
    assert r.status_code == 200
    data = r.json()
    assert "anomalies" in data
    assert isinstance(data["anomalies"], list)


@pytest.mark.asyncio
async def test_soc_alerts_schema(admin_client: AsyncClient):
    r = await admin_client.get("/api/v1/monitoring/soc/alerts")
    assert r.status_code == 200
    data = r.json()
    assert "alerts" in data
    assert isinstance(data["alerts"], list)


@pytest.mark.asyncio
async def test_soc_alerts_severity_values(admin_client: AsyncClient):
    r = await admin_client.get("/api/v1/monitoring/soc/alerts")
    assert r.status_code == 200
    alerts = r.json().get("alerts", [])
    valid_severities = {"info", "low", "warning", "medium", "high", "critical"}
    for alert in alerts:
        sev = str(alert.get("severity", "")).lower()
        assert sev in valid_severities, f"Unexpected severity: {sev}"


# ── Devices & Sessions ────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_devices_me_returns_list(user_client: AsyncClient):
    r = await user_client.get("/api/v1/devices/me")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


@pytest.mark.asyncio
async def test_sessions_me_returns_list(user_client: AsyncClient):
    r = await user_client.get("/api/v1/devices/me/sessions")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


@pytest.mark.asyncio
async def test_device_events_me_returns_list(user_client: AsyncClient):
    r = await user_client.get("/api/v1/devices/me/events")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


@pytest.mark.asyncio
async def test_admin_all_devices_returns_list(admin_client: AsyncClient):
    r = await admin_client.get("/api/v1/devices/admin")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


@pytest.mark.asyncio
async def test_admin_all_device_events_returns_list(admin_client: AsyncClient):
    r = await admin_client.get("/api/v1/devices/admin/events")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


@pytest.mark.asyncio
async def test_device_schema_fields(admin_client: AsyncClient):
    r = await admin_client.get("/api/v1/devices/admin")
    assert r.status_code == 200
    devices = r.json()
    for d in devices:
        assert "id" in d
        assert "user_id" in d
        assert "trust_score" in d
        assert "status" in d
        assert "risk_level" in d
        assert "is_revoked" in d


# ── Firewall ──────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_firewall_clients_list(admin_client: AsyncClient):
    r = await admin_client.get("/api/v1/firewall/clients")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


@pytest.mark.asyncio
async def test_firewall_client_schema(admin_client: AsyncClient):
    r = await admin_client.get("/api/v1/firewall/clients")
    assert r.status_code == 200
    clients = r.json()
    for c in clients:
        assert "id" in c
        assert "client_id" in c
        assert "name" in c
        assert "is_active" in c
        assert "trust_score" in c


# ── ZTA / Policy engine ───────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_zta_status_returns_dict(admin_client: AsyncClient):
    r = await admin_client.get("/api/v1/monitoring/zta/status")
    assert r.status_code == 200
    assert isinstance(r.json(), dict)


@pytest.mark.asyncio
async def test_policy_simulation_benign_prompt(admin_client: AsyncClient):
    r = await admin_client.post(
        "/api/v1/security/policy/simulate",
        json={"prompt": "What is the capital of France?", "model_id": 1},
    )
    assert r.status_code in (200, 404, 422)
    if r.status_code == 200:
        data = r.json()
        assert isinstance(data, dict)


# ── Trust profile ─────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_user_trust_rate_profile(admin_client: AsyncClient):
    r = await admin_client.get("/api/v1/monitoring/users/suite-test-user/rate")
    assert r.status_code in (200, 404)
    if r.status_code == 200:
        data = r.json()
        assert isinstance(data, dict)


@pytest.mark.asyncio
async def test_all_user_trust_profiles(admin_client: AsyncClient):
    r = await admin_client.get("/api/v1/monitoring/users/trust/all")
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, (list, dict))


# ── Research / Reporting ──────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_reporting_research_metrics(admin_client: AsyncClient):
    r = await admin_client.get("/api/v1/reporting/research-metrics")
    assert r.status_code == 200
    assert isinstance(r.json(), dict)


@pytest.mark.asyncio
async def test_monitoring_research_summary(user_client: AsyncClient):
    r = await user_client.get("/api/v1/monitoring/research/summary")
    assert r.status_code == 200
    assert isinstance(r.json(), dict)
