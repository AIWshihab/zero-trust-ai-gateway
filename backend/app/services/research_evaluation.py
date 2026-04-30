from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.policy_engine import evaluate_request
from app.models.attack_sequence_event import AttackSequenceEvent
from app.models.request_log import RequestLog
from app.models.security import SecurityControl
from app.schemas import RequestDecision

RESEARCH_EVALUATION_LIMIT = 5000
DECISION_ORDER = {"allow": 0, "challenge": 1, "block": 2}


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:
        return default


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except Exception:
        return default


def _normalize_decision(value: Any) -> str:
    if hasattr(value, "value"):
        return str(value.value).lower()
    return str(value or "allow").lower()


def _event_time(value: datetime | None) -> datetime:
    if value is None:
        return datetime.now(timezone.utc)
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


def _bucket_key(value: datetime | None, bucket: str) -> str:
    timestamp = _event_time(value)
    if bucket == "daily":
        return timestamp.strftime("%Y-%m-%d")
    return timestamp.strftime("%Y-%m-%dT%H:00:00Z")


def _extract_policy_inputs(log: RequestLog) -> dict[str, Any]:
    trace = log.decision_trace or {}
    snapshot = log.decision_input_snapshot or {}
    inputs = trace.get("inputs") or snapshot.get("policy_inputs") or {}

    model_base_risk = inputs.get("model_base_risk_score")
    if model_base_risk is None:
        model_base_risk = snapshot.get("model_base_risk_score")

    return {
        "model_risk_score": _safe_float(inputs.get("model_risk_score"), 0.0),
        "sensitivity_score": _safe_float(inputs.get("sensitivity_score"), 0.0),
        "prompt_risk_score": _safe_float(inputs.get("prompt_risk_score"), log.prompt_risk_score or 0.0),
        "request_rate_score": _safe_float(inputs.get("request_rate_score"), 0.0),
        "user_trust_penalty": _safe_float(inputs.get("user_trust_penalty"), 0.0),
        "secure_mode_enabled": bool(inputs.get("secure_mode_enabled", log.secure_mode_enabled)),
        "recent_risky_events": _safe_int(inputs.get("recent_risky_events"), 0),
        "recent_blocks": _safe_int(inputs.get("recent_blocks"), 0),
        "recent_challenges": _safe_int(inputs.get("recent_challenges"), 0),
        "model_base_risk_score": model_base_risk,
        "secured_model_risk_score": inputs.get("secured_model_risk_score"),
        "control_effectiveness_score": inputs.get("control_effectiveness_score"),
        "attack_sequence_severity": _safe_float(inputs.get("attack_sequence_severity"), 0.0),
        "repeated_pattern_count": _safe_int(inputs.get("repeated_pattern_count"), 0),
        "cross_model_abuse_score": _safe_float(inputs.get("cross_model_abuse_score"), 0.0),
    }


def _policy_decision_from_thresholds(score: float, challenge: float, block: float) -> str:
    if score >= block:
        return "block"
    if score >= challenge:
        return "challenge"
    return "allow"


def _simulate_log_decision(log: RequestLog, *, mode: str = "current") -> dict[str, Any]:
    policy = evaluate_request(**_extract_policy_inputs(log))
    score = _safe_float(policy.get("security_score"), log.security_score)
    thresholds = policy.get("effective_thresholds") or {}
    challenge = _safe_float(thresholds.get("challenge"), 0.45)
    block = _safe_float(thresholds.get("block"), 0.75)

    if mode == "stricter":
        challenge = max(0.05, challenge - 0.08)
        block = max(challenge + 0.05, block - 0.08)
    elif mode == "relaxed":
        challenge = min(0.95, challenge + 0.08)
        block = min(1.0, max(challenge + 0.05, block + 0.08))

    return {
        "decision": _policy_decision_from_thresholds(score, challenge, block),
        "security_score": round(score, 4),
        "thresholds": {
            "challenge": round(challenge, 4),
            "block": round(block, 4),
        },
        "adaptive_reasons": policy.get("adaptive_reasons") or [],
    }


def _summarize_replay(logs: list[RequestLog], *, mode: str) -> dict[str, Any]:
    counts = Counter()
    changed = 0
    stricter_changes = 0
    relaxed_changes = 0
    risk_total = 0.0

    for log in logs:
        simulated = _simulate_log_decision(log, mode=mode)
        decision = simulated["decision"]
        original = _normalize_decision(log.decision)
        counts[decision] += 1
        risk_total += _safe_float(simulated["security_score"])
        if decision != original:
            changed += 1
            if DECISION_ORDER.get(decision, 0) > DECISION_ORDER.get(original, 0):
                stricter_changes += 1
            elif DECISION_ORDER.get(decision, 0) < DECISION_ORDER.get(original, 0):
                relaxed_changes += 1

    total = len(logs)
    return {
        "mode": mode,
        "total_requests": total,
        "allowed": counts.get("allow", 0),
        "challenged": counts.get("challenge", 0),
        "blocked": counts.get("block", 0),
        "block_rate": round(counts.get("block", 0) / total, 4) if total else 0.0,
        "average_risk": round(risk_total / total, 4) if total else 0.0,
        "difference_vs_original": {
            "changed_decisions": changed,
            "stricter_decisions": stricter_changes,
            "relaxed_decisions": relaxed_changes,
        },
    }


def _formal_risk_metrics(logs: list[RequestLog]) -> dict[str, Any]:
    distribution = {
        "0.00-0.20": 0,
        "0.20-0.40": 0,
        "0.40-0.60": 0,
        "0.60-0.80": 0,
        "0.80-1.00": 0,
    }
    decision_risk: dict[str, list[float]] = {"allow": [], "challenge": [], "block": []}
    consistency_matches = 0
    effective_total = 0.0
    previous_total = 0.0

    for log in logs:
        simulated = _simulate_log_decision(log, mode="current")
        trace = log.decision_trace or {}
        effective = _safe_float(trace.get("effective_risk"), simulated["security_score"])
        previous = _safe_float(log.security_score, simulated["security_score"])
        effective_total += effective
        previous_total += previous

        if effective < 0.20:
            distribution["0.00-0.20"] += 1
        elif effective < 0.40:
            distribution["0.20-0.40"] += 1
        elif effective < 0.60:
            distribution["0.40-0.60"] += 1
        elif effective < 0.80:
            distribution["0.60-0.80"] += 1
        else:
            distribution["0.80-1.00"] += 1

        actual = _normalize_decision(log.decision)
        decision_risk.setdefault(actual, []).append(effective)
        expected = "block" if effective >= 0.70 else "challenge" if effective >= 0.45 else "allow"
        if DECISION_ORDER.get(actual, 0) >= DECISION_ORDER.get(expected, 0):
            consistency_matches += 1

    total = len(logs)
    avg_by_decision = {
        decision: round(sum(values) / len(values), 4) if values else 0.0
        for decision, values in decision_risk.items()
    }
    return {
        "effective_risk_distribution": distribution,
        "correlation_between_effective_risk_and_decisions": {
            "average_effective_risk_by_decision": avg_by_decision,
            "ordered_decision_expectation": "allow < challenge < block should show increasing average effective risk",
        },
        "comparison_with_previous_risk_model": {
            "average_effective_risk": round(effective_total / total, 4) if total else 0.0,
            "average_previous_security_score": round(previous_total / total, 4) if total else 0.0,
            "average_delta": round((effective_total - previous_total) / total, 4) if total else 0.0,
        },
        "decision_consistency_metrics": {
            "consistent_or_stricter_count": consistency_matches,
            "total_requests": total,
            "consistent_or_stricter_rate": round(consistency_matches / total, 4) if total else 0.0,
        },
    }


async def build_policy_replay(db: AsyncSession, *, limit: int = RESEARCH_EVALUATION_LIMIT) -> dict[str, Any]:
    logs = list(
        (
            await db.execute(
                select(RequestLog).order_by(RequestLog.timestamp.desc()).limit(limit)
            )
        ).scalars().all()
    )
    logs.reverse()

    return {
        "source": "request_logs.decision_trace",
        "inference_rerun": False,
        "modes": [
            _summarize_replay(logs, mode="current"),
            _summarize_replay(logs, mode="stricter"),
            _summarize_replay(logs, mode="relaxed"),
        ],
        "formal_risk_evaluation": _formal_risk_metrics(logs),
    }


def _control_ids_for_log(log: RequestLog) -> set[str]:
    trace = log.decision_trace or {}
    snapshot = log.decision_input_snapshot or {}
    reason = f"{log.reason or ''} {trace.get('reason') or ''}".lower()
    flags = " ".join(snapshot.get("prompt_flags") or snapshot.get("flags") or [])
    dynamic_matches = str(snapshot.get("dynamic_rule_matches") or "")
    adaptive = " ".join(str(item) for item in (trace.get("adaptive_reasons") or []))
    evidence = f"{reason} {flags} {dynamic_matches} {adaptive}".lower()
    inputs = trace.get("inputs") or {}

    controls: set[str] = set()
    if any(token in evidence for token in ("injection", "ignore", "override")):
        controls.add("LLM01")
    if any(token in evidence for token in ("secret", "credential", "api_key", "private_key", "sensitive")):
        controls.add("LLM02")
    if _safe_float(inputs.get("model_base_risk_score"), 0.0) >= 50:
        controls.add("LLM03")
    if "posture" in evidence or "poison" in evidence:
        controls.add("LLM04")
    if "output" in evidence or _safe_float(log.output_risk_score, 0.0) > 0:
        controls.add("LLM05")
    if "challenge" in evidence or _normalize_decision(log.decision) == "challenge":
        controls.add("LLM06")
    if any(token in evidence for token in ("system_prompt", "prompt leak", "extraction")):
        controls.add("LLM07")
    if "retrieval" in evidence or "embedding" in evidence or "rag" in evidence:
        controls.add("LLM08")
    if "misinformation" in evidence or "citation" in evidence:
        controls.add("LLM09")
    if any(token in evidence for token in ("rate", "cooldown", "repeated", "abuse", "cross_model")):
        controls.add("LLM10")
    if log.secure_mode_enabled:
        controls.add("LLM06")
    return controls


async def build_control_effectiveness(db: AsyncSession, *, limit: int = RESEARCH_EVALUATION_LIMIT) -> dict[str, Any]:
    controls = list(
        (
            await db.execute(select(SecurityControl).where(SecurityControl.enabled.is_(True)).order_by(SecurityControl.control_id.asc()))
        ).scalars().all()
    )
    logs = list(
        (
            await db.execute(select(RequestLog).order_by(RequestLog.timestamp.desc()).limit(limit))
        ).scalars().all()
    )
    enforcement_logs = [log for log in logs if _normalize_decision(log.decision) in {"challenge", "block"}]
    contribution_counts = Counter()

    for log in enforcement_logs:
        for control_id in _control_ids_for_log(log):
            contribution_counts[control_id] += 1

    denominator = max(1, len(enforcement_logs))
    return {
        "source": "request_logs.decision_trace + security_controls",
        "total_enforcement_decisions": len(enforcement_logs),
        "controls": [
            {
                "control_id": control.control_id,
                "control_name": control.name,
                "coverage": control.coverage,
                "contribution_count": contribution_counts.get(control.control_id, 0),
                "contribution_percentage": round(contribution_counts.get(control.control_id, 0) / denominator, 4),
            }
            for control in controls
        ],
    }


def _counterfactual_policy(log: RequestLog, *, remove: str) -> dict[str, Any]:
    inputs = _extract_policy_inputs(log)
    if remove == "adaptive_thresholds":
        inputs["attack_sequence_severity"] = 0.0
        inputs["repeated_pattern_count"] = 0
        inputs["cross_model_abuse_score"] = 0.0
        inputs["recent_risky_events"] = 0
        inputs["recent_blocks"] = 0
        inputs["recent_challenges"] = 0
        inputs["secure_mode_enabled"] = False
    elif remove == "cross_model_abuse_detection":
        inputs["cross_model_abuse_score"] = 0.0
    elif remove == "trust_based_adjustment":
        inputs["user_trust_penalty"] = 0.0
    policy = evaluate_request(**inputs)
    return {
        "decision": _normalize_decision(policy["decision"]),
        "security_score": policy["security_score"],
        "adaptive_reasons": policy.get("adaptive_reasons") or [],
        "effective_thresholds": policy.get("effective_thresholds") or {},
    }


async def build_counterfactual_analysis(db: AsyncSession, *, limit: int = 250) -> dict[str, Any]:
    logs = list(
        (
            await db.execute(select(RequestLog).order_by(RequestLog.timestamp.desc()).limit(limit))
        ).scalars().all()
    )
    scenarios = ("adaptive_thresholds", "cross_model_abuse_detection", "trust_based_adjustment")
    differences = Counter()
    examples: list[dict[str, Any]] = []

    for log in logs:
        original = _normalize_decision(log.decision)
        per_log = {}
        for scenario in scenarios:
            result = _counterfactual_policy(log, remove=scenario)
            changed = result["decision"] != original
            if changed:
                differences[scenario] += 1
            per_log[scenario] = {
                "counterfactual_decision": result["decision"],
                "changed": changed,
                "reason_for_difference": (
                    f"Decision changed when {scenario.replace('_', ' ')} was removed."
                    if changed
                    else "No decision change under this counterfactual."
                ),
            }
        if any(item["changed"] for item in per_log.values()) and len(examples) < 25:
            examples.append(
                {
                    "log_id": log.id,
                    "model_id": log.model_id,
                    "original_decision": original,
                    "counterfactuals": per_log,
                }
            )

    return {
        "source": "request_logs.decision_trace",
        "total_requests_analyzed": len(logs),
        "difference_counts": dict(differences),
        "examples": examples,
    }


async def build_risk_drift(db: AsyncSession, *, bucket: str = "hourly", limit: int = RESEARCH_EVALUATION_LIMIT) -> dict[str, Any]:
    bucket = "daily" if bucket == "daily" else "hourly"
    logs = list(
        (
            await db.execute(select(RequestLog).order_by(RequestLog.timestamp.desc()).limit(limit))
        ).scalars().all()
    )
    events = list(
        (
            await db.execute(select(AttackSequenceEvent).order_by(AttackSequenceEvent.timestamp.desc()).limit(limit))
        ).scalars().all()
    )

    buckets: dict[str, dict[str, Any]] = defaultdict(
        lambda: {
            "request_count": 0,
            "blocked": 0,
            "challenged": 0,
            "allowed": 0,
            "risk_total": 0.0,
            "trust_penalty_total": 0.0,
            "trust_samples": 0,
            "attack_event_count": 0,
            "attack_severity_total": 0.0,
        }
    )

    for log in logs:
        key = _bucket_key(log.timestamp, bucket)
        row = buckets[key]
        decision = _normalize_decision(log.decision)
        row["request_count"] += 1
        if decision == "block":
            row["blocked"] += 1
        elif decision == "challenge":
            row["challenged"] += 1
        else:
            row["allowed"] += 1
        row["risk_total"] += _safe_float(log.security_score)
        inputs = (log.decision_trace or {}).get("inputs") or {}
        row["trust_penalty_total"] += _safe_float(inputs.get("user_trust_penalty"), 0.0)
        row["trust_samples"] += 1

    for event in events:
        key = _bucket_key(event.timestamp, bucket)
        row = buckets[key]
        row["attack_event_count"] += 1
        row["attack_severity_total"] += _safe_float(event.sequence_severity)

    series = []
    for key in sorted(buckets):
        row = buckets[key]
        request_count = row["request_count"]
        attack_count = row["attack_event_count"]
        series.append(
            {
                "bucket": key,
                "request_count": request_count,
                "allowed": row["allowed"],
                "challenged": row["challenged"],
                "blocked": row["blocked"],
                "block_rate": round(row["blocked"] / request_count, 4) if request_count else 0.0,
                "average_risk": round(row["risk_total"] / request_count, 4) if request_count else 0.0,
                "average_user_trust_penalty": round(row["trust_penalty_total"] / row["trust_samples"], 4) if row["trust_samples"] else 0.0,
                "attack_sequence_intensity": round(row["attack_severity_total"] / attack_count, 4) if attack_count else 0.0,
                "attack_event_count": attack_count,
            }
        )

    return {
        "bucket": bucket,
        "source": "request_logs + attack_sequence_events",
        "series": series,
        "summary": {
            "bucket_count": len(series),
            "latest": series[-1] if series else None,
        },
    }
