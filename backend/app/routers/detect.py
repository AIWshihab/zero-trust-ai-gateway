import time

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.policy_engine import evaluate_request
from app.core.rate_limiter import get_request_rate_score, record_request
from app.core.security import hash_prompt, require_active_user
from app.core.trust_score import (
    get_behavior_context,
    record_behavior_event,
)
from app.core.config import get_settings
from app.models.model import Model

from app.schemas import (
    ErrorResponse,
    TokenData,
    DetectRequest,
    DetectResponse,
    InferenceRequest,
    InferenceResponse,
    RequestDecision,
)
from app.services.model_registry import (
    get_model_risk_score,
    get_model_sensitivity_score,
)
from app.services.prompt_guard import evaluate_prompt_guard, GuardDecision
from app.services.model_router import route_to_model
from app.services.db_logger import log_request_db
from app.services.model_readiness import ensure_model_ready
from app.services.reassessment_service import (
    get_user_trust_penalty_persistent,
    reassess_model_posture,
    reassess_user_trust_on_request,
)

router = APIRouter()


def _map_guard_decision_to_request_decision(guard_decision: GuardDecision) -> RequestDecision:
    if guard_decision == GuardDecision.BLOCK:
        return RequestDecision.BLOCK
    if guard_decision == GuardDecision.CHALLENGE:
        return RequestDecision.CHALLENGE
    return RequestDecision.ALLOW


def _safe_float(value) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except Exception:
        return None


def _model_base_risk_score(model) -> float | None:
    persisted = _safe_float(getattr(model, "base_risk_score", None))
    if persisted is not None:
        return max(0.0, min(100.0, persisted))

    base_trust = _safe_float(getattr(model, "base_trust_score", None))
    if base_trust is None:
        return None

    return max(0.0, min(100.0, 100.0 - base_trust))


def _decision_snapshot(
    *,
    policy_result: dict,
    prompt_result,
    behavior_context: dict,
    model_base_risk_score: float | None,
    secure_mode_enabled: bool,
    request_rate_score: float,
    final_decision: RequestDecision,
) -> tuple[dict, dict]:
    prompt_guard_decision = (
        prompt_result.decision.value
        if hasattr(prompt_result.decision, "value")
        else str(prompt_result.decision)
    )

    decision_input_snapshot = {
        "secure_mode_enabled": bool(secure_mode_enabled),
        "model_base_risk_score": model_base_risk_score,
        "policy_inputs": policy_result.get("inputs", {}),
        "effective_thresholds": policy_result.get("effective_thresholds", {}),
        "adaptive_reasons": policy_result.get("adaptive_reasons", []),
        "behavior_context": behavior_context,
        "prompt_guard": {
            "decision": prompt_guard_decision,
            "prompt_risk_score": float(getattr(prompt_result, "prompt_risk_score", 0.0)),
            "flags": list(getattr(prompt_result, "flags", [])),
        },
        "request_rate_score": round(float(request_rate_score), 4),
    }

    decision_trace = {
        "policy_decision": policy_result.get("decision").value if hasattr(policy_result.get("decision"), "value") else str(policy_result.get("decision")),
        "guard_decision": prompt_guard_decision,
        "final_decision": final_decision.value,
        "adaptive_reasons": policy_result.get("adaptive_reasons", []),
        "secure_mode_enabled": bool(secure_mode_enabled),
    }

    return decision_input_snapshot, decision_trace


# ─── Prompt Detection Only (no inference) ────────────────────────────────────

@router.post(
    "/",
    response_model=DetectResponse,
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        404: {"model": ErrorResponse, "description": "Model not found"},
    },
)
async def detect_prompt(
    payload: DetectRequest,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(require_active_user),
):
    """
    Analyses a prompt for risk without routing to a model.
    Used by the frontend to pre-screen user input.
    """
    model_id = payload.model_id or 1

    model = (
        await db.execute(select(Model).where(Model.id == model_id))
    ).scalar_one_or_none()
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Model {model_id} not found",
        )

    await reassess_model_posture(
        db,
        model_row=model,
        trigger="prompt_detection_precheck",
        request_context={"decision": "allow", "secure_mode_enabled": bool(model.secure_mode_enabled)},
        commit=False,
    )

    request_rate_score = get_request_rate_score(current_user.username)
    user_trust_penalty = await get_user_trust_penalty_persistent(
        db,
        user_id=current_user.user_id,
        username=current_user.username,
    )
    user_trust_score = max(0.0, 1.0 - user_trust_penalty)
    behavior_context = get_behavior_context(current_user.username)
    model_base_risk_score = _model_base_risk_score(model)

    model_sensitivity_label = (
        model.sensitivity_level.value
        if hasattr(model.sensitivity_level, "value")
        else str(model.sensitivity_level)
    )

    prompt_result = await evaluate_prompt_guard(
        payload.prompt,
        user_trust_score=user_trust_score,
        model_sensitivity=model_sensitivity_label,
        provider=model.provider_name,
    )

    model_risk_score = (
        max(0.0, min(1.0, model_base_risk_score / 100.0))
        if model_base_risk_score is not None
        else await get_model_risk_score(db=db, model_id=model_id)
    )
    sensitivity_score = await get_model_sensitivity_score(db=db, model_id=model_id)

    policy = evaluate_request(
        model_risk_score=model_risk_score,
        sensitivity_score=sensitivity_score,
        prompt_risk_score=prompt_result.prompt_risk_score,
        request_rate_score=request_rate_score,
        user_trust_penalty=user_trust_penalty,
        secure_mode_enabled=bool(model.secure_mode_enabled),
        recent_risky_events=behavior_context.get("recent_risky_events", 0),
        recent_blocks=behavior_context.get("recent_blocks", 0),
        recent_challenges=behavior_context.get("recent_challenges", 0),
        model_base_risk_score=model_base_risk_score,
    )

    policy_decision = policy["decision"]
    policy_reason = policy["reason"]

    # Respect a hard block from the guard layer
    if prompt_result.decision == GuardDecision.BLOCK and policy_decision != RequestDecision.BLOCK:
        policy_decision = RequestDecision.BLOCK
        policy_reason = f"{policy_reason} | Guard blocked: {prompt_result.reason}"

    elif prompt_result.decision == GuardDecision.CHALLENGE and policy_decision == RequestDecision.ALLOW:
        policy_decision = RequestDecision.CHALLENGE
        policy_reason = f"{policy_reason} | Guard challenge: {prompt_result.reason}"

    else:
        policy_reason = f"{policy_reason} | Guard: {prompt_result.reason}"

    # Track risk behavior from pre-screening activity for adaptive secure mode.
    trust_update = await reassess_user_trust_on_request(
        db,
        user_id=current_user.user_id,
        username=current_user.username,
        decision=policy_decision,
        prompt_risk_score=prompt_result.prompt_risk_score,
        security_score=float(policy.get("security_score", 0.0)),
        request_rate_score=request_rate_score,
        secure_mode_enabled=bool(model.secure_mode_enabled),
        behavior_context=behavior_context,
        reason_prefix="Prompt detection outcome reassessment.",
        commit=False,
    )
    record_behavior_event(
        current_user.username,
        policy_decision,
        prompt_risk_score=prompt_result.prompt_risk_score,
        security_score=float(policy.get("security_score", 0.0)),
        request_rate_score=request_rate_score,
        secure_mode_enabled=bool(model.secure_mode_enabled),
    )
    await reassess_model_posture(
        db,
        model_row=model,
        trigger="prompt_detection_outcome",
        request_context={
            "decision": policy_decision.value,
            "request_rate_score": request_rate_score,
            "prompt_risk_score": prompt_result.prompt_risk_score,
            "security_score": float(policy.get("security_score", 0.0)),
            "secure_mode_enabled": bool(model.secure_mode_enabled),
            "trust_update": trust_update,
        },
        commit=True,
    )

    return DetectResponse(
        prompt_risk_score=prompt_result.prompt_risk_score,
        flags=prompt_result.flags,
        decision=policy_decision,
        reason=policy_reason,
    )


# ─── Full Inference Request ───────────────────────────────────────────────────

@router.post(
    "/infer",
    response_model=InferenceResponse,
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Model inactive or forbidden"},
        409: {"model": ErrorResponse, "description": "Model not ready"},
        404: {"model": ErrorResponse, "description": "Model not found"},
        500: {"model": ErrorResponse, "description": "Inference failed"},
    },
)
async def infer(
    payload: InferenceRequest,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(require_active_user),
):
    start_time = time.time()
    parameters = payload.parameters or {}
    current_settings = get_settings()

    # ── Step 1: Validate model ─────────────────────────────────────────────
    model = (
        await db.execute(select(Model).where(Model.id == payload.model_id))
    ).scalar_one_or_none()
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Model {payload.model_id} not found",
        )
    if not model.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Model {payload.model_id} is inactive",
        )
    ensure_model_ready(model, action="inference")
    secure_mode_enabled = bool(model.secure_mode_enabled)
    await reassess_model_posture(
        db,
        model_row=model,
        trigger="request_precheck",
        request_context={"decision": "allow", "secure_mode_enabled": secure_mode_enabled},
        commit=False,
    )

    # ── Step 2: Record request for rate limiter ────────────────────────────
    record_request(current_user.username)

    # ── Step 3: ZTA Toggle ─────────────────────────────────────────────────
    if not current_settings.ZTA_ENABLED:
        output = await route_to_model(model, payload.prompt, parameters)
        latency_ms = round((time.time() - start_time) * 1000, 2)

        record_behavior_event(
            current_user.username,
            RequestDecision.ALLOW,
            prompt_risk_score=0.0,
            security_score=0.0,
            request_rate_score=get_request_rate_score(current_user.username),
            secure_mode_enabled=secure_mode_enabled,
        )
        await reassess_user_trust_on_request(
            db,
            user_id=current_user.user_id,
            username=current_user.username,
            decision=RequestDecision.ALLOW,
            prompt_risk_score=0.0,
            security_score=0.0,
            request_rate_score=get_request_rate_score(current_user.username),
            secure_mode_enabled=secure_mode_enabled,
            behavior_context=get_behavior_context(current_user.username),
            reason_prefix="ZTA disabled pass-through request.",
            commit=False,
        )
        await reassess_model_posture(
            db,
            model_row=model,
            trigger="request_outcome",
            request_context={
                "decision": RequestDecision.ALLOW.value,
                "request_rate_score": get_request_rate_score(current_user.username),
                "prompt_risk_score": 0.0,
                "security_score": 0.0,
                "secure_mode_enabled": secure_mode_enabled,
            },
            commit=False,
        )

        await log_request_db(
            db,
            user_id=current_user.user_id,
            model_id=payload.model_id,
            prompt_hash=hash_prompt(payload.prompt),
            security_score=0.0,
            decision=RequestDecision.ALLOW,
            latency_ms=latency_ms,
            prompt_risk_score=0.0,
            output_risk_score=0.0,
            secure_mode_enabled=secure_mode_enabled,
            reason="ZTA disabled — request passed through without evaluation",
            decision_input_snapshot={
                "secure_mode_enabled": secure_mode_enabled,
                "zta_enabled": False,
            },
            decision_trace={
                "policy_decision": "allow",
                "guard_decision": "not_evaluated",
                "final_decision": "allow",
                "adaptive_reasons": [],
            },
        )

        return InferenceResponse(
            model_id=payload.model_id,
            output=output,
            decision=RequestDecision.ALLOW,
            security_score=0.0,
            blocked=False,
            reason="ZTA disabled — request passed through without evaluation",
            latency_ms=latency_ms,
        )

    # ── Step 4: ZTA ON — full security pipeline ────────────────────────────
    rate_score = get_request_rate_score(current_user.username)
    trust_penalty = await get_user_trust_penalty_persistent(
        db,
        user_id=current_user.user_id,
        username=current_user.username,
    )
    user_trust_score = max(0.0, 1.0 - trust_penalty)
    behavior_context = get_behavior_context(current_user.username)
    model_base_risk_score = _model_base_risk_score(model)

    model_risk_score = (
        max(0.0, min(1.0, model_base_risk_score / 100.0))
        if model_base_risk_score is not None
        else await get_model_risk_score(db=db, model_id=payload.model_id)
    )
    sensitivity_score = await get_model_sensitivity_score(db=db, model_id=payload.model_id)

    model_sensitivity_label = (
        model.sensitivity_level.value
        if hasattr(model.sensitivity_level, "value")
        else str(model.sensitivity_level)
    )

    prompt_result = await evaluate_prompt_guard(
        payload.prompt,
        user_trust_score=user_trust_score,
        model_sensitivity=model_sensitivity_label,
        provider=model.provider_name,
    )

    policy = evaluate_request(
        model_risk_score=model_risk_score,
        sensitivity_score=sensitivity_score,
        prompt_risk_score=prompt_result.prompt_risk_score,
        request_rate_score=rate_score,
        user_trust_penalty=trust_penalty,
        secure_mode_enabled=secure_mode_enabled,
        recent_risky_events=behavior_context.get("recent_risky_events", 0),
        recent_blocks=behavior_context.get("recent_blocks", 0),
        recent_challenges=behavior_context.get("recent_challenges", 0),
        model_base_risk_score=model_base_risk_score,
    )

    decision = policy["decision"]
    security_score = policy["security_score"]
    reason = policy["reason"]

    # Respect guard outcome if stricter than policy engine
    if prompt_result.decision == GuardDecision.BLOCK and decision != RequestDecision.BLOCK:
        decision = RequestDecision.BLOCK
        security_score = max(security_score, prompt_result.prompt_risk_score)
        reason = f"{reason} | Guard blocked: {prompt_result.reason}"

    elif prompt_result.decision == GuardDecision.CHALLENGE and decision == RequestDecision.ALLOW:
        decision = RequestDecision.CHALLENGE
        security_score = max(security_score, prompt_result.prompt_risk_score)
        reason = f"{reason} | Guard challenge: {prompt_result.reason}"

    else:
        reason = f"{reason} | Guard: {prompt_result.reason}"

    decision_input_snapshot, decision_trace = _decision_snapshot(
        policy_result=policy,
        prompt_result=prompt_result,
        behavior_context=behavior_context,
        model_base_risk_score=model_base_risk_score,
        secure_mode_enabled=secure_mode_enabled,
        request_rate_score=rate_score,
        final_decision=decision,
    )

    # ── Step 5: Persist trust reassessment ─────────────────────────────────
    trust_update = await reassess_user_trust_on_request(
        db,
        user_id=current_user.user_id,
        username=current_user.username,
        decision=decision,
        prompt_risk_score=prompt_result.prompt_risk_score,
        security_score=security_score,
        request_rate_score=rate_score,
        secure_mode_enabled=secure_mode_enabled,
        behavior_context=behavior_context,
        commit=False,
    )
    record_behavior_event(
        current_user.username,
        decision,
        prompt_risk_score=prompt_result.prompt_risk_score,
        security_score=security_score,
        request_rate_score=rate_score,
        secure_mode_enabled=secure_mode_enabled,
    )
    await reassess_model_posture(
        db,
        model_row=model,
        trigger="request_outcome",
        request_context={
            "decision": decision.value,
            "request_rate_score": rate_score,
            "prompt_risk_score": prompt_result.prompt_risk_score,
            "security_score": security_score,
            "secure_mode_enabled": secure_mode_enabled,
        },
        commit=False,
    )

    latency_ms = round((time.time() - start_time) * 1000, 2)

    # ── Step 6: Enforce decision ───────────────────────────────────────────
    if decision == RequestDecision.BLOCK:
        await log_request_db(
            db,
            user_id=current_user.user_id,
            model_id=payload.model_id,
            prompt_hash=hash_prompt(payload.prompt),
            security_score=security_score,
            decision=decision,
            latency_ms=latency_ms,
            prompt_risk_score=prompt_result.prompt_risk_score,
            output_risk_score=0.0,
            blocked=True,
            secure_mode_enabled=secure_mode_enabled,
            reason=reason,
            decision_input_snapshot={**decision_input_snapshot, "trust_update": trust_update},
            decision_trace=decision_trace,
        )
        return InferenceResponse(
            model_id=payload.model_id,
            output=None,
            decision=decision,
            security_score=security_score,
            blocked=True,
            reason=reason,
            latency_ms=latency_ms,
        )

    if decision == RequestDecision.CHALLENGE:
        reason += " | Challenge issued — additional verification required"

    # ── Step 7: Route to model ─────────────────────────────────────────────
    output = await route_to_model(model, payload.prompt, parameters)
    latency_ms = round((time.time() - start_time) * 1000, 2)

    # ── Step 8: Log request ────────────────────────────────────────────────
    await log_request_db(
        db,
        user_id=current_user.user_id,
        model_id=payload.model_id,
        prompt_hash=hash_prompt(payload.prompt),
        security_score=security_score,
        decision=decision,
        latency_ms=latency_ms,
        prompt_risk_score=prompt_result.prompt_risk_score,
        output_risk_score=0.0,
        blocked=False,
        secure_mode_enabled=secure_mode_enabled,
        reason=reason,
        decision_input_snapshot={**decision_input_snapshot, "trust_update": trust_update},
        decision_trace=decision_trace,
    )

    return InferenceResponse(
        model_id=payload.model_id,
        output=output,
        decision=decision,
        security_score=security_score,
        blocked=False,
        reason=reason,
        latency_ms=latency_ms,
    )
