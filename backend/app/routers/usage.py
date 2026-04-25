import time

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.output_guard import inspect_output
from app.core.policy_engine import evaluate_request
from app.core.rate_limiter import (
    record_request,
    get_request_rate_score,
    get_penalty_profile,
    is_rate_limited,
    record_abuse_outcome,
)
from app.core.security import require_active_user, hash_prompt
from app.core.trust_score import (
    get_behavior_context,
    record_behavior_event,
)
from app.models.model import Model
from app.schemas import (
    ErrorResponse,
    InferenceRequest,
    SafeInferenceResponse,
    RequestDecision,
    TokenData,
)
from app.services.model_readiness import ensure_model_ready
from app.services.db_logger import log_request_db
from app.services.model_router import route_to_model
from app.services.prompt_guard import evaluate_prompt_guard, GuardDecision
from app.services.reassessment_service import (
    get_user_trust_penalty_persistent,
    reassess_model_posture,
    reassess_user_trust_on_request,
)
from app.services.security_catalog import list_detection_rules

router = APIRouter()


def _sensitivity_to_score(value) -> float:
    if hasattr(value, "value"):
        value = value.value

    normalized = str(value or "medium").lower()
    mapping = {
        "low": 0.2,
        "medium": 0.5,
        "high": 0.8,
        "critical": 1.0,
    }
    return mapping.get(normalized, 0.5)


def _guard_to_request_decision(value: GuardDecision) -> RequestDecision:
    if value == GuardDecision.BLOCK:
        return RequestDecision.BLOCK
    if value == GuardDecision.CHALLENGE:
        return RequestDecision.CHALLENGE
    return RequestDecision.ALLOW


def _safe_float(value) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except Exception:
        return None


def _model_base_risk_score(model_row: Model) -> float | None:
    persisted = _safe_float(model_row.base_risk_score)
    if persisted is not None:
        return max(0.0, min(100.0, persisted))

    if model_row.base_trust_score is None:
        return None

    try:
        return max(0.0, min(100.0, 100.0 - float(model_row.base_trust_score)))
    except Exception:
        return None


def _decision_snapshot(
    *,
    policy_result: dict,
    guard_result,
    behavior_context: dict,
    model_base_risk_score: float | None,
    secure_mode_enabled: bool,
    request_rate_score: float,
    policy_decision: RequestDecision,
    final_decision: RequestDecision,
) -> tuple[dict, dict]:
    guard_decision = guard_result.decision.value if hasattr(guard_result.decision, "value") else str(guard_result.decision)

    decision_input_snapshot = {
        "secure_mode_enabled": bool(secure_mode_enabled),
        "model_base_risk_score": model_base_risk_score,
        "policy_inputs": policy_result.get("inputs", {}),
        "effective_thresholds": policy_result.get("effective_thresholds", {}),
        "adaptive_reasons": policy_result.get("adaptive_reasons", []),
        "behavior_context": behavior_context,
        "guard": {
            "decision": guard_decision,
            "prompt_risk_score": float(getattr(guard_result, "prompt_risk_score", 0.0)),
            "flags": list(getattr(guard_result, "flags", [])),
        },
        "request_rate_score": round(float(request_rate_score), 4),
    }

    decision_trace = {
        "policy_decision": policy_decision.value,
        "guard_decision": guard_decision,
        "final_decision": final_decision.value,
        "adaptive_reasons": policy_result.get("adaptive_reasons", []),
        "secure_mode_enabled": bool(secure_mode_enabled),
    }

    return decision_input_snapshot, decision_trace


@router.post(
    "/infer",
    response_model=SafeInferenceResponse,
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Model inactive"},
        409: {"model": ErrorResponse, "description": "Model not ready"},
        404: {"model": ErrorResponse, "description": "Model not found"},
        500: {"model": ErrorResponse, "description": "Inference failed"},
    },
)
async def safe_infer(
    payload: InferenceRequest,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(require_active_user),
):
    started = time.perf_counter()
    username = current_user.username

    result = await db.execute(select(Model).where(Model.id == payload.model_id))
    model_row = result.scalar_one_or_none()

    if not model_row:
        raise HTTPException(status_code=404, detail="Model not found")
    if not bool(model_row.is_active):
        raise HTTPException(status_code=403, detail="Model is inactive")
    ensure_model_ready(model_row, action="inference")

    model_sensitivity = (
        model_row.sensitivity_level.value
        if hasattr(model_row.sensitivity_level, "value")
        else str(model_row.sensitivity_level or "medium")
    )
    secure_mode_enabled = bool(model_row.secure_mode_enabled)

    # Continuous reassessment pre-check: apply stale/drift posture adjustments
    # before we evaluate this request.
    await reassess_model_posture(
        db,
        model_row=model_row,
        trigger="request_precheck",
        request_context={
            "decision": "allow",
            "secure_mode_enabled": secure_mode_enabled,
        },
        commit=False,
    )

    penalty_profile = get_penalty_profile(username)
    if penalty_profile.get("penalty_active"):
        latency_ms = (time.perf_counter() - started) * 1000.0
        decision = RequestDecision.BLOCK
        remaining = int(penalty_profile.get("cooldown_remaining_seconds") or 0)
        reason = f"Temporary abuse penalty active. Retry after {remaining} second(s)."
        behavior_context = get_behavior_context(username)

        trust_update = await reassess_user_trust_on_request(
            db,
            user_id=current_user.user_id,
            username=username,
            decision=decision,
            prompt_risk_score=1.0,
            security_score=1.0,
            request_rate_score=get_request_rate_score(username),
            secure_mode_enabled=secure_mode_enabled,
            behavior_context=behavior_context,
            reason_prefix="Temporary abuse penalty blocked request.",
            commit=False,
        )
        updated_behavior_context = record_behavior_event(
            username,
            decision,
            prompt_risk_score=1.0,
            security_score=1.0,
            request_rate_score=get_request_rate_score(username),
            secure_mode_enabled=secure_mode_enabled,
        )
        await reassess_model_posture(
            db,
            model_row=model_row,
            trigger="request_outcome",
            request_context={
                "decision": decision.value,
                "request_rate_score": get_request_rate_score(username),
                "prompt_risk_score": 1.0,
                "security_score": 1.0,
                "secure_mode_enabled": secure_mode_enabled,
                "penalty_profile": penalty_profile,
            },
            commit=False,
        )

        await log_request_db(
            db,
            user_id=current_user.user_id,
            model_id=model_row.id,
            prompt_hash=hash_prompt(payload.prompt),
            security_score=1.0,
            decision=decision,
            latency_ms=latency_ms,
            prompt_risk_score=1.0,
            output_risk_score=0.0,
            blocked=True,
            secure_mode_enabled=secure_mode_enabled,
            reason=reason,
            decision_input_snapshot={
                "secure_mode_enabled": secure_mode_enabled,
                "behavior_context_before": behavior_context,
                "behavior_context_after": updated_behavior_context,
                "trust_update": trust_update,
                "penalty_profile": penalty_profile,
            },
            decision_trace={
                "policy_decision": "block",
                "guard_decision": "not_evaluated",
                "final_decision": "block",
                "adaptive_reasons": ["temporary abuse penalty active"],
                "secure_mode_enabled": secure_mode_enabled,
            },
        )

        return SafeInferenceResponse(
            model_id=model_row.id,
            output=None,
            decision=decision,
            security_score=1.0,
            prompt_risk_score=1.0,
            output_risk_score=0.0,
            blocked=True,
            reason=reason,
            latency_ms=latency_ms,
            secure_mode_enabled=secure_mode_enabled,
            enforcement_profile=penalty_profile,
        )

    # Hard rate limit fast-path
    if is_rate_limited(username):
        latency_ms = (time.perf_counter() - started) * 1000.0
        decision = RequestDecision.BLOCK
        reason = "Blocked by hard rate limit."
        behavior_context = get_behavior_context(username)
        penalty_profile = record_abuse_outcome(
            username,
            decision=decision.value,
            prompt_risk_score=0.0,
            security_score=1.0,
            reason=reason,
        )

        trust_update = await reassess_user_trust_on_request(
            db,
            user_id=current_user.user_id,
            username=username,
            decision=decision,
            prompt_risk_score=0.0,
            security_score=1.0,
            request_rate_score=1.0,
            secure_mode_enabled=secure_mode_enabled,
            behavior_context=behavior_context,
            reason_prefix="Hard rate limit triggered immediate trust reassessment.",
            commit=False,
        )
        updated_behavior_context = record_behavior_event(
            username,
            decision,
            prompt_risk_score=0.0,
            security_score=1.0,
            request_rate_score=1.0,
            secure_mode_enabled=secure_mode_enabled,
        )
        await reassess_model_posture(
            db,
            model_row=model_row,
            trigger="request_outcome",
            request_context={
                "decision": decision.value,
                "request_rate_score": 1.0,
                "prompt_risk_score": 0.0,
                "security_score": 1.0,
                "secure_mode_enabled": secure_mode_enabled,
            },
            commit=False,
        )

        await log_request_db(
            db,
            user_id=current_user.user_id,
            model_id=model_row.id,
            prompt_hash=hash_prompt(payload.prompt),
            security_score=1.0,
            decision=decision,
            latency_ms=latency_ms,
            prompt_risk_score=0.0,
            output_risk_score=0.0,
            blocked=True,
            secure_mode_enabled=secure_mode_enabled,
            reason=reason,
            decision_input_snapshot={
                "secure_mode_enabled": secure_mode_enabled,
                "request_rate_score": 1.0,
                "behavior_context_before": behavior_context,
                "behavior_context_after": updated_behavior_context,
                "trust_update": trust_update,
                "penalty_profile": penalty_profile,
            },
            decision_trace={
                "policy_decision": "block",
                "guard_decision": "not_evaluated",
                "final_decision": "block",
                "adaptive_reasons": ["hard rate limit triggered immediate block"],
                "secure_mode_enabled": secure_mode_enabled,
            },
        )

        return SafeInferenceResponse(
            model_id=model_row.id,
            output=None,
            decision=decision,
            security_score=1.0,
            prompt_risk_score=0.0,
            output_risk_score=0.0,
            blocked=True,
            reason=reason,
            latency_ms=latency_ms,
            secure_mode_enabled=secure_mode_enabled,
            enforcement_profile=penalty_profile,
        )

    # Record request for sliding-window rate score
    record_request(username)
    request_rate_score = get_request_rate_score(username)
    user_trust_penalty = await get_user_trust_penalty_persistent(
        db,
        user_id=current_user.user_id,
        username=username,
    )
    behavior_context = get_behavior_context(username)

    guard_result = await evaluate_prompt_guard(
        payload.prompt,
        user_trust_score=max(0.0, 1.0 - user_trust_penalty),
        model_sensitivity=model_sensitivity,
        provider=model_row.provider_name,
        dynamic_rules=await list_detection_rules(db, target="prompt"),
    )

    prompt_risk_score = float(guard_result.prompt_risk_score)

    model_base_risk_score = _model_base_risk_score(model_row)
    model_risk_score = 0.5
    if model_base_risk_score is not None:
        model_risk_score = max(0.0, min(1.0, model_base_risk_score / 100.0))
    elif model_row.base_trust_score is not None:
        model_risk_score = max(0.0, min(1.0, 1.0 - (float(model_row.base_trust_score) / 100.0)))

    policy_result = evaluate_request(
        model_risk_score=model_risk_score,
        sensitivity_score=_sensitivity_to_score(model_row.sensitivity_level),
        prompt_risk_score=prompt_risk_score,
        request_rate_score=request_rate_score,
        user_trust_penalty=user_trust_penalty,
        secure_mode_enabled=secure_mode_enabled,
        recent_risky_events=behavior_context.get("recent_risky_events", 0),
        recent_blocks=behavior_context.get("recent_blocks", 0),
        recent_challenges=behavior_context.get("recent_challenges", 0),
        model_base_risk_score=model_base_risk_score,
    )

    policy_decision = policy_result.get("decision", RequestDecision.ALLOW)
    policy_reason = policy_result.get("reason", "Policy evaluation completed")
    security_score = float(policy_result.get("security_score", prompt_risk_score))

    guard_decision = _guard_to_request_decision(guard_result.decision)

    if guard_decision == RequestDecision.BLOCK or policy_decision == RequestDecision.BLOCK:
        final_decision = RequestDecision.BLOCK
    elif guard_decision == RequestDecision.CHALLENGE or policy_decision == RequestDecision.CHALLENGE:
        final_decision = RequestDecision.CHALLENGE
    else:
        final_decision = RequestDecision.ALLOW

    if final_decision == RequestDecision.BLOCK:
        final_reason = f"Blocked by gateway policy. {guard_result.reason} | {policy_reason}"
    elif final_decision == RequestDecision.CHALLENGE:
        final_reason = f"Challenged by gateway policy. {guard_result.reason} | {policy_reason}"
    else:
        final_reason = f"Allowed by gateway policy. {policy_reason} | PromptGuard: {guard_result.reason}"

    decision_input_snapshot, decision_trace = _decision_snapshot(
        policy_result=policy_result,
        guard_result=guard_result,
        behavior_context=behavior_context,
        model_base_risk_score=model_base_risk_score,
        secure_mode_enabled=secure_mode_enabled,
        request_rate_score=request_rate_score,
        policy_decision=policy_decision,
        final_decision=final_decision,
    )

    if final_decision == RequestDecision.BLOCK:
        latency_ms = (time.perf_counter() - started) * 1000.0
        penalty_profile = record_abuse_outcome(
            username,
            decision=final_decision.value,
            prompt_risk_score=prompt_risk_score,
            security_score=security_score,
            reason=final_reason,
        )

        trust_update = await reassess_user_trust_on_request(
            db,
            user_id=current_user.user_id,
            username=username,
            decision=final_decision,
            prompt_risk_score=prompt_risk_score,
            security_score=security_score,
            request_rate_score=request_rate_score,
            secure_mode_enabled=secure_mode_enabled,
            behavior_context=behavior_context,
            commit=False,
        )
        record_behavior_event(
            username,
            final_decision,
            prompt_risk_score=prompt_risk_score,
            security_score=security_score,
            request_rate_score=request_rate_score,
            secure_mode_enabled=secure_mode_enabled,
        )
        await reassess_model_posture(
            db,
            model_row=model_row,
            trigger="request_outcome",
            request_context={
                "decision": final_decision.value,
                "request_rate_score": request_rate_score,
                "prompt_risk_score": prompt_risk_score,
                "security_score": security_score,
                "secure_mode_enabled": secure_mode_enabled,
                "penalty_profile": penalty_profile,
            },
            commit=False,
        )

        await log_request_db(
            db,
            user_id=current_user.user_id,
            model_id=model_row.id,
            prompt_hash=hash_prompt(payload.prompt),
            security_score=security_score,
            decision=final_decision,
            latency_ms=latency_ms,
            prompt_risk_score=prompt_risk_score,
            output_risk_score=0.0,
            blocked=True,
            secure_mode_enabled=secure_mode_enabled,
            reason=final_reason,
            decision_input_snapshot={**decision_input_snapshot, "trust_update": trust_update, "penalty_profile": penalty_profile},
            decision_trace=decision_trace,
        )

        return SafeInferenceResponse(
            model_id=model_row.id,
            output=None,
            decision=final_decision,
            security_score=security_score,
            prompt_risk_score=prompt_risk_score,
            output_risk_score=0.0,
            blocked=True,
            reason=final_reason,
            latency_ms=latency_ms,
            secure_mode_enabled=secure_mode_enabled,
            enforcement_profile=penalty_profile,
        )

    try:
        output_text = await route_to_model(
            model=model_row,
            prompt=payload.prompt,
            parameters=payload.parameters,
        )
    except HTTPException as exc:
        latency_ms = (time.perf_counter() - started) * 1000.0

        trust_update = await reassess_user_trust_on_request(
            db,
            user_id=current_user.user_id,
            username=username,
            decision=RequestDecision.BLOCK,
            prompt_risk_score=prompt_risk_score,
            security_score=max(security_score, prompt_risk_score),
            request_rate_score=request_rate_score,
            secure_mode_enabled=secure_mode_enabled,
            behavior_context=behavior_context,
            reason_prefix="Upstream provider failure forced protective block.",
            commit=False,
        )
        record_behavior_event(
            username,
            RequestDecision.BLOCK,
            prompt_risk_score=prompt_risk_score,
            security_score=max(security_score, prompt_risk_score),
            request_rate_score=request_rate_score,
            secure_mode_enabled=secure_mode_enabled,
        )
        await reassess_model_posture(
            db,
            model_row=model_row,
            trigger="request_outcome",
            request_context={
                "decision": RequestDecision.BLOCK.value,
                "request_rate_score": request_rate_score,
                "prompt_risk_score": prompt_risk_score,
                "security_score": max(security_score, prompt_risk_score),
                "secure_mode_enabled": secure_mode_enabled,
            },
            commit=False,
        )

        await log_request_db(
            db,
            user_id=current_user.user_id,
            model_id=model_row.id,
            prompt_hash=hash_prompt(payload.prompt),
            security_score=max(security_score, prompt_risk_score),
            decision=RequestDecision.BLOCK,
            latency_ms=latency_ms,
            prompt_risk_score=prompt_risk_score,
            output_risk_score=0.0,
            blocked=True,
            secure_mode_enabled=secure_mode_enabled,
            reason=f"Upstream error: {exc.detail}",
            decision_input_snapshot={**decision_input_snapshot, "trust_update": trust_update},
            decision_trace={
                **decision_trace,
                "final_decision": RequestDecision.BLOCK.value,
                "error_type": "upstream_http_exception",
                "error_detail": str(exc.detail),
            },
        )
        raise
    except Exception as exc:
        latency_ms = (time.perf_counter() - started) * 1000.0

        trust_update = await reassess_user_trust_on_request(
            db,
            user_id=current_user.user_id,
            username=username,
            decision=RequestDecision.BLOCK,
            prompt_risk_score=prompt_risk_score,
            security_score=max(security_score, prompt_risk_score),
            request_rate_score=request_rate_score,
            secure_mode_enabled=secure_mode_enabled,
            behavior_context=behavior_context,
            reason_prefix="Inference runtime failure forced protective block.",
            commit=False,
        )
        record_behavior_event(
            username,
            RequestDecision.BLOCK,
            prompt_risk_score=prompt_risk_score,
            security_score=max(security_score, prompt_risk_score),
            request_rate_score=request_rate_score,
            secure_mode_enabled=secure_mode_enabled,
        )
        await reassess_model_posture(
            db,
            model_row=model_row,
            trigger="request_outcome",
            request_context={
                "decision": RequestDecision.BLOCK.value,
                "request_rate_score": request_rate_score,
                "prompt_risk_score": prompt_risk_score,
                "security_score": max(security_score, prompt_risk_score),
                "secure_mode_enabled": secure_mode_enabled,
            },
            commit=False,
        )

        await log_request_db(
            db,
            user_id=current_user.user_id,
            model_id=model_row.id,
            prompt_hash=hash_prompt(payload.prompt),
            security_score=max(security_score, prompt_risk_score),
            decision=RequestDecision.BLOCK,
            latency_ms=latency_ms,
            prompt_risk_score=prompt_risk_score,
            output_risk_score=0.0,
            blocked=True,
            secure_mode_enabled=secure_mode_enabled,
            reason=f"Inference failed: {exc}",
            decision_input_snapshot={**decision_input_snapshot, "trust_update": trust_update},
            decision_trace={
                **decision_trace,
                "final_decision": RequestDecision.BLOCK.value,
                "error_type": "inference_exception",
                "error_detail": str(exc),
            },
        )
        raise HTTPException(status_code=500, detail=f"Inference failed: {exc}")

    output_guard_result = inspect_output(
        output_text,
        dynamic_rules=await list_detection_rules(db, target="output"),
    )
    output_action = output_guard_result.get("action", "allow")
    output_risk_score = float(output_guard_result.get("risk_score", 0.0))
    output_findings = output_guard_result.get("findings", [])

    final_output = output_text
    blocked = False

    if secure_mode_enabled:
        if output_action == "block":
            final_output = None
            blocked = True
            final_decision = RequestDecision.BLOCK
            final_reason = "Blocked by output guard."
        elif output_action == "redact":
            final_output = output_guard_result.get("redacted_text") or "[REDACTED BY OUTPUT GUARD]"
            final_reason = "Response redacted by output guard."

    if output_findings:
        final_reason = f"{final_reason} " + "; ".join(output_findings)

    latency_ms = (time.perf_counter() - started) * 1000.0
    combined_security_score = max(
        security_score,
        prompt_risk_score,
        min(1.0, output_risk_score / 100.0),
    )
    penalty_profile = record_abuse_outcome(
        username,
        decision=final_decision.value,
        prompt_risk_score=prompt_risk_score,
        security_score=combined_security_score,
        reason=final_reason,
    )

    trust_update = await reassess_user_trust_on_request(
        db,
        user_id=current_user.user_id,
        username=username,
        decision=final_decision,
        prompt_risk_score=prompt_risk_score,
        security_score=combined_security_score,
        request_rate_score=request_rate_score,
        secure_mode_enabled=secure_mode_enabled,
        behavior_context=behavior_context,
        commit=False,
    )
    record_behavior_event(
        username,
        final_decision,
        prompt_risk_score=prompt_risk_score,
        security_score=combined_security_score,
        request_rate_score=request_rate_score,
        secure_mode_enabled=secure_mode_enabled,
    )
    await reassess_model_posture(
        db,
        model_row=model_row,
        trigger="request_outcome",
        request_context={
            "decision": final_decision.value,
            "request_rate_score": request_rate_score,
            "prompt_risk_score": prompt_risk_score,
            "security_score": combined_security_score,
            "secure_mode_enabled": secure_mode_enabled,
            "penalty_profile": penalty_profile,
        },
        commit=False,
    )

    decision_trace["final_decision"] = final_decision.value
    decision_trace["output_guard_action"] = output_action
    decision_trace["output_guard_findings"] = output_findings

    await log_request_db(
        db,
        user_id=current_user.user_id,
        model_id=model_row.id,
        prompt_hash=hash_prompt(payload.prompt),
        security_score=combined_security_score,
        decision=final_decision,
        latency_ms=latency_ms,
        prompt_risk_score=prompt_risk_score,
        output_risk_score=output_risk_score,
        blocked=blocked,
        secure_mode_enabled=secure_mode_enabled,
        reason=final_reason,
        decision_input_snapshot={**decision_input_snapshot, "trust_update": trust_update, "penalty_profile": penalty_profile},
        decision_trace=decision_trace,
    )

    return SafeInferenceResponse(
        model_id=model_row.id,
        output=final_output,
        decision=final_decision,
        security_score=combined_security_score,
        prompt_risk_score=prompt_risk_score,
        output_risk_score=output_risk_score,
        blocked=blocked,
        reason=final_reason,
        latency_ms=latency_ms,
        secure_mode_enabled=secure_mode_enabled,
        enforcement_profile=penalty_profile,
    )
