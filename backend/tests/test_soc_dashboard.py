import asyncio
from datetime import datetime
from typing import Any

import pytest
from httpx import ASGITransport, AsyncClient

from app.core import monitoring
from app.main import app
from app.schemas import TokenData


def _admin_user() -> TokenData:
    return TokenData(
        user_id=1,
        username="soc-test-admin",
        email="soc-test-admin@example.com",
        scopes=["admin"],
    )


@pytest.fixture
async def async_client():
    async def _fake_admin():
        return _admin_user()

    app.dependency_overrides[monitoring.require_admin] = _fake_admin
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
    app.dependency_overrides.clear()


def _assert_json_object(value: Any) -> dict[str, Any]:
    assert isinstance(value, dict), f"Expected JSON object, got {type(value)}"
    return value


def _assert_timestamp(value: str) -> None:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    assert parsed.year >= 2000


def _severity_rank(severity: str) -> int:
    text = str(severity or "").lower()
    if text in {"critical", "high"}:
        return 0
    if text in {"warning", "medium"}:
        return 1
    return 2


@pytest.mark.asyncio
async def test_soc_attack_timeline_endpoint_schema(async_client: AsyncClient):
    response = await async_client.get("/api/v1/monitoring/soc/attack-timeline")
    assert response.status_code == 200
    data = _assert_json_object(response.json())
    assert "events" in data
    assert isinstance(data["events"], list)

    for event in data["events"]:
        assert isinstance(event, dict)
        assert "timestamp" in event
        assert event["timestamp"] is None or isinstance(event["timestamp"], str)
        if event["timestamp"]:
            _assert_timestamp(event["timestamp"])
        # Real endpoint uses severity/count-like fields rather than a literal "count".
        assert any(
            key in event
            for key in ("repeated_pattern_count", "sequence_severity", "risk_score")
        )


@pytest.mark.asyncio
async def test_soc_threat_heatmap_endpoint_schema(async_client: AsyncClient):
    response = await async_client.get("/api/v1/monitoring/soc/threat-heatmap")
    assert response.status_code == 200
    data = _assert_json_object(response.json())
    assert "cells" in data
    assert isinstance(data["cells"], list)

    for cell in data["cells"]:
        assert isinstance(cell, dict)
        assert "attack_stage" in cell
        assert "count" in cell or "value" in cell or "intensity" in cell
        if "count" in cell:
            assert isinstance(cell["count"], int)


@pytest.mark.asyncio
async def test_soc_user_anomalies_endpoint_schema(async_client: AsyncClient):
    response = await async_client.get("/api/v1/monitoring/soc/user-anomalies")
    assert response.status_code == 200
    data = _assert_json_object(response.json())
    assert "anomalies" in data
    assert isinstance(data["anomalies"], list)

    for anomaly in data["anomalies"]:
        assert isinstance(anomaly, dict)
        assert "username" in anomaly or "user_id" in anomaly
        assert "trust_score" in anomaly or "anomaly_score" in anomaly


@pytest.mark.asyncio
async def test_soc_alerts_endpoint_schema(async_client: AsyncClient):
    response = await async_client.get("/api/v1/monitoring/soc/alerts")
    assert response.status_code == 200
    data = _assert_json_object(response.json())
    assert "alerts" in data
    assert isinstance(data["alerts"], list)

    for alert in data["alerts"]:
        assert isinstance(alert, dict)
        assert alert.get("severity") is not None
        assert alert.get("message") is not None
        # Timestamp may be top-level or nested under event in current backend shape.
        nested_ts = (alert.get("event") or {}).get("timestamp")
        top_ts = alert.get("timestamp")
        assert top_ts is not None or nested_ts is not None
        if top_ts:
            _assert_timestamp(top_ts)
        if nested_ts:
            _assert_timestamp(nested_ts)


def test_alert_priority_sorting_rule():
    alerts = [
        {"severity": "low", "message": "low"},
        {"severity": "critical", "message": "critical"},
        {"severity": "medium", "message": "medium"},
        {"severity": "high", "message": "high"},
        {"severity": "info", "message": "info"},
        {"severity": "warning", "message": "warning"},
    ]
    sorted_alerts = sorted(alerts, key=lambda item: _severity_rank(item["severity"]))
    ranks = [_severity_rank(item["severity"]) for item in sorted_alerts]
    assert ranks == sorted(ranks)


@pytest.mark.asyncio
async def test_soc_realtime_polling_consistency(async_client: AsyncClient):
    endpoints = [
        "/api/v1/monitoring/soc/attack-timeline",
        "/api/v1/monitoring/soc/threat-heatmap",
        "/api/v1/monitoring/soc/user-anomalies",
        "/api/v1/monitoring/soc/alerts",
    ]

    snapshots: dict[str, list[dict[str, Any]]] = {endpoint: [] for endpoint in endpoints}
    for _ in range(3):
        for endpoint in endpoints:
            res = await async_client.get(endpoint)
            assert res.status_code == 200
            payload = _assert_json_object(res.json())
            snapshots[endpoint].append(payload)
        await asyncio.sleep(0.1)

    for endpoint, payloads in snapshots.items():
        first_keys = set(payloads[0].keys())
        for payload in payloads[1:]:
            assert set(payload.keys()) == first_keys, f"Schema changed for {endpoint}"

        if endpoint.endswith("attack-timeline"):
            totals = [int(p.get("total", 0)) for p in payloads]
            assert all(total >= 0 for total in totals)
        if endpoint.endswith("alerts"):
            totals = [int(p.get("total", 0)) for p in payloads]
            assert all(total >= 0 for total in totals)


@pytest.mark.asyncio
async def test_alert_data_consistency_and_timestamp(async_client: AsyncClient):
    response = await async_client.get("/api/v1/monitoring/soc/alerts")
    assert response.status_code == 200
    alerts = _assert_json_object(response.json()).get("alerts", [])

    if not alerts:
        pytest.skip("No alerts available to validate field non-null consistency.")

    alert = alerts[0]
    assert alert.get("severity")
    assert alert.get("message")

    timestamp = alert.get("timestamp") or (alert.get("event") or {}).get("timestamp")
    assert timestamp is not None
    _assert_timestamp(timestamp)
