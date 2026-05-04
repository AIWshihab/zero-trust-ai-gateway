from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_prompt
from app.evaluation.evaluation_metrics import compare_metrics, compute_metrics
from app.evaluation.scenarios import AttackScenario, AttackStep
from app.models.request_log import RequestLog
from app.services.prompt_guard import analyze_prompt


def _snapshot_trust(log: RequestLog) -> float | None:
    snapshot = log.decision_input_snapshot or {}
    trace = log.decision_trace or {}
    for key in ("trust_score", "user_trust"):
        if key in snapshot:
            return float(snapshot[key])
        if key in trace:
            return float(trace[key])
    factors = trace.get("factors") if isinstance(trace, dict) else None
    if isinstance(factors, dict) and factors.get("user_trust") is not None:
        return float(factors["user_trust"])
    return None


def evaluate_baseline(step: AttackStep) -> dict[str, Any]:
    """Simulate a weak baseline: static prompt guard only, no trust/adaptation."""
    result = analyze_prompt(step.prompt)
    decision = str(result["decision"])
    # A weak system challenges but often forwards after a user click, so only hard blocks count as stopped.
    stopped = decision == "block"
    return {
        "step": step.step,
        "prompt": step.prompt,
        "expected_malicious": step.expected_malicious,
        "tactic": step.tactic,
        "decision": decision,
        "risk_score": result["risk_score"],
        "trust_score": 1.0,
        "stopped": stopped,
        "reason": result["reason"],
        "evidence": {
            "mode": "baseline_static_prompt_guard",
            "flags": result["flags"],
            "adaptive_controls": False,
        },
    }


async def _latest_log_for_prompt(
    db: AsyncSession,
    *,
    prompt: str,
    user_id: int | None,
) -> RequestLog | None:
    query = select(RequestLog).where(RequestLog.prompt_hash == hash_prompt(prompt))
    if user_id is not None:
        query = query.where(RequestLog.user_id == user_id)
    query = query.order_by(RequestLog.timestamp.desc()).limit(1)
    return (await db.execute(query)).scalar_one_or_none()


async def evaluate_with_gateway(
    db: AsyncSession,
    step: AttackStep,
    *,
    user_id: int | None,
) -> dict[str, Any]:
    """Read the latest real gateway decision for this scenario step from logs."""
    log = await _latest_log_for_prompt(db, prompt=step.prompt, user_id=user_id)
    if log is None:
        return {
            "step": step.step,
            "prompt": step.prompt,
            "expected_malicious": step.expected_malicious,
            "tactic": step.tactic,
            "decision": "missing_evidence",
            "risk_score": 0.0,
            "trust_score": None,
            "stopped": False,
            "reason": "No matching gateway log found. Run this scenario through the gateway to generate evidence.",
            "evidence": {
                "mode": "gateway_from_existing_logs",
                "prompt_hash": hash_prompt(step.prompt),
                "log_found": False,
            },
        }

    decision = str(log.decision or "unknown").lower()
    return {
        "step": step.step,
        "prompt": step.prompt,
        "expected_malicious": step.expected_malicious,
        "tactic": step.tactic,
        "decision": decision,
        "risk_score": float(log.prompt_risk_score or log.security_score or 0.0),
        "trust_score": _snapshot_trust(log),
        "stopped": decision in {"block", "challenge"},
        "reason": log.reason,
        "evidence": {
            "mode": "gateway_from_existing_logs",
            "log_found": True,
            "log_id": log.id,
            "model_id": log.model_id,
            "prompt_hash": log.prompt_hash,
            "security_score": log.security_score,
            "prompt_risk_score": log.prompt_risk_score,
            "output_risk_score": log.output_risk_score,
            "decision_input_snapshot": log.decision_input_snapshot,
            "decision_trace": log.decision_trace,
            "timestamp": log.timestamp.isoformat() if log.timestamp else None,
        },
    }


def _first_stopped_step(results: list[dict[str, Any]]) -> int | None:
    for row in results:
        if row.get("expected_malicious") and row.get("stopped"):
            return int(row["step"])
    return None


def _policy_impact(baseline_results: list[dict[str, Any]], gateway_results: list[dict[str, Any]]) -> dict[str, Any]:
    baseline_stop = _first_stopped_step(baseline_results)
    gateway_stop = _first_stopped_step(gateway_results)
    traces = [
        row.get("evidence", {}).get("decision_trace") or {}
        for row in gateway_results
        if row.get("evidence", {}).get("log_found")
    ]
    trust_seen = any(
        "trust" in str(trace).lower() or row.get("trust_score") is not None
        for trace, row in zip(traces, gateway_results)
    )
    cross_model_seen = any("model" in str(trace).lower() for trace in traces)
    penalty_seen = any("penalty" in str(trace).lower() or "cooldown" in str(trace).lower() for trace in traces)

    return {
        "baseline_stop_step": baseline_stop,
        "gateway_stop_step": gateway_stop,
        "trust_scoring": "Evidence present in decision trace" if trust_seen else "No trust evidence found in matched logs",
        "cross_model_detection": "Model context present in trace/logs" if cross_model_seen else "No cross-model evidence found in matched logs",
        "adaptive_penalties": "Penalty/cooldown evidence present" if penalty_seen else "No adaptive penalty evidence found in matched logs",
        "summary": (
            f"Gateway stopped attack at step {gateway_stop}."
            if gateway_stop
            else "Gateway evidence is incomplete for this scenario."
        ),
    }


async def compare_scenario(
    db: AsyncSession,
    scenario: AttackScenario,
    *,
    user_id: int | None,
) -> dict[str, Any]:
    baseline_results = [evaluate_baseline(step) for step in scenario.steps]
    gateway_results = [
        await evaluate_with_gateway(db, step, user_id=user_id)
        for step in scenario.steps
    ]
    baseline_metrics = compute_metrics(baseline_results)
    gateway_metrics = compute_metrics(gateway_results)
    return {
        "scenario": {
            "id": scenario.id,
            "name": scenario.name,
            "objective": scenario.objective,
        },
        "baseline": {
            "mode": "simple_prompt_guard_only",
            "metrics": baseline_metrics,
            "results": baseline_results,
        },
        "gateway": {
            "mode": "existing_gateway_logs",
            "metrics": gateway_metrics,
            "results": gateway_results,
        },
        "improvement": compare_metrics(baseline_metrics, gateway_metrics),
        "policy_impact": _policy_impact(baseline_results, gateway_results),
    }
