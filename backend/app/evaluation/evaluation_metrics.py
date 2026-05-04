from __future__ import annotations

from statistics import mean
from typing import Any


ENFORCED_DECISIONS = {"block", "challenge"}


def _as_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:
        return default


def _decision(value: Any) -> str:
    return str(value or "unknown").lower()


def compute_metrics(results: list[dict[str, Any]]) -> dict[str, float]:
    total = max(1, len(results))
    malicious = [row for row in results if bool(row.get("expected_malicious"))]
    benign = [row for row in results if not bool(row.get("expected_malicious"))]
    malicious_total = max(1, len(malicious))
    benign_total = max(1, len(benign))

    detected = [row for row in malicious if _decision(row.get("decision")) in ENFORCED_DECISIONS]
    blocked = [row for row in results if _decision(row.get("decision")) == "block"]
    challenged = [row for row in results if _decision(row.get("decision")) == "challenge"]
    false_positive = [row for row in benign if _decision(row.get("decision")) in ENFORCED_DECISIONS]
    risks = [_as_float(row.get("risk_score")) for row in results]
    trust_values = [
        _as_float(row.get("trust_score"))
        for row in results
        if row.get("trust_score") is not None
    ]

    trust_decay_rate = 0.0
    if len(trust_values) >= 2:
        trust_decay_rate = max(0.0, trust_values[0] - trust_values[-1])

    return {
        "total_steps": float(len(results)),
        "detection_rate": round(len(detected) / malicious_total, 4),
        "block_rate": round(len(blocked) / total, 4),
        "challenge_rate": round(len(challenged) / total, 4),
        "false_positive_rate": round(len(false_positive) / benign_total, 4) if benign else 0.0,
        "average_risk_score": round(mean(risks) if risks else 0.0, 4),
        "trust_decay_rate": round(trust_decay_rate, 4),
    }


def compare_metrics(baseline: dict[str, float], gateway: dict[str, float]) -> dict[str, float]:
    return {
        "detection_rate_delta": round(gateway.get("detection_rate", 0.0) - baseline.get("detection_rate", 0.0), 4),
        "block_rate_delta": round(gateway.get("block_rate", 0.0) - baseline.get("block_rate", 0.0), 4),
        "challenge_rate_delta": round(gateway.get("challenge_rate", 0.0) - baseline.get("challenge_rate", 0.0), 4),
        "false_positive_rate_delta": round(gateway.get("false_positive_rate", 0.0) - baseline.get("false_positive_rate", 0.0), 4),
        "risk_score_delta": round(gateway.get("average_risk_score", 0.0) - baseline.get("average_risk_score", 0.0), 4),
        "trust_decay_delta": round(gateway.get("trust_decay_rate", 0.0) - baseline.get("trust_decay_rate", 0.0), 4),
    }
