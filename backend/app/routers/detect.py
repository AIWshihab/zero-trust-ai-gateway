import time

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.policy_engine import evaluate_request
from app.core.rate_limiter import get_request_rate_score, record_request
from app.core.security import hash_prompt, require_active_user
from app.core.trust_score import get_user_trust_penalty, update_trust_score
from app.core.config import get_settings

from app.models.schemas import (
    TokenData,
    DetectRequest,
    DetectResponse,
    InferenceRequest,
    InferenceResponse,
    RequestDecision,
)
from app.models.registry import (
    get_model,
    get_model_risk_score,
    get_model_sensitivity_score,
)
from app.services.prompt_guard import evaluate_prompt_guard, GuardDecision
from app.services.model_router import route_to_model
from app.services.logger import log_request

router = APIRouter()
settings = get_settings()


def _map_guard_decision_to_request_decision(guard_decision: GuardDecision) -> RequestDecision:
    if guard_decision == GuardDecision.BLOCK:
        return RequestDecision.BLOCK
    if guard_decision == GuardDecision.CHALLENGE:
        return RequestDecision.CHALLENGE
    return RequestDecision.ALLOW


# ─── Prompt Detection Only (no inference) ────────────────────────────────────

@router.post("/", response_model=DetectResponse)
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

    prompt_result = await evaluate_prompt_guard(
        payload.prompt,
        user_trust_score=1.0,  # replace later if you store normalized trust on the user
        model_sensitivity="medium",
    )

    model_risk_score = await get_model_risk_score(db=db, model_id=model_id)
    sensitivity_score = await get_model_sensitivity_score(db=db, model_id=model_id)

    policy = evaluate_request(
        model_risk_score=model_risk_score,
        sensitivity_score=sensitivity_score,
        prompt_risk_score=prompt_result.prompt_risk_score,
        request_rate_score=get_request_rate_score(current_user.username),
        user_trust_penalty=get_user_trust_penalty(current_user.username),
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

    return DetectResponse(
        prompt_risk_score=prompt_result.prompt_risk_score,
        flags=prompt_result.flags,
        decision=policy_decision,
        reason=policy_reason,
    )


# ─── Full Inference Request ───────────────────────────────────────────────────

@router.post("/infer", response_model=InferenceResponse)
async def infer(
    payload: InferenceRequest,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(require_active_user),
):
    start_time = time.time()
    parameters = payload.parameters or {}
    print(payload.prompt)

    # ── Step 1: Validate model ─────────────────────────────────────────────
    model = await get_model(db=db, model_id=payload.model_id)
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

    # ── Step 2: Record request for rate limiter ────────────────────────────
    record_request(current_user.username)

    # ── Step 3: ZTA Toggle ─────────────────────────────────────────────────
    if not settings.ZTA_ENABLED:
        output = await route_to_model(model, payload.prompt, parameters)
        latency_ms = round((time.time() - start_time) * 1000, 2)

        await log_request(
            user_id=current_user.username,
            model_id=payload.model_id,
            prompt_hash=hash_prompt(payload.prompt),
            security_score=0.0,
            decision=RequestDecision.ALLOW,
            latency_ms=latency_ms,
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
    trust_penalty = get_user_trust_penalty(current_user.username)

    model_risk_score = await get_model_risk_score(db=db, model_id=payload.model_id)
    sensitivity_score = await get_model_sensitivity_score(db=db, model_id=payload.model_id)

    model_sensitivity_label = (
        model.sensitivity_level.value
        if hasattr(model.sensitivity_level, "value")
        else str(model.sensitivity_level)
    )

    prompt_result = await evaluate_prompt_guard(
        payload.prompt,
        user_trust_score=1.0,  # replace later if you expose normalized trust on the user
        model_sensitivity=model_sensitivity_label,
    )

    policy = evaluate_request(
        model_risk_score=model_risk_score,
        sensitivity_score=sensitivity_score,
        prompt_risk_score=prompt_result.prompt_risk_score,
        request_rate_score=rate_score,
        user_trust_penalty=trust_penalty,
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

    # ── Step 5: Update trust score ─────────────────────────────────────────
    update_trust_score(current_user.username, decision)

    latency_ms = round((time.time() - start_time) * 1000, 2)

    # ── Step 6: Enforce decision ───────────────────────────────────────────
    if decision == RequestDecision.BLOCK:
        await log_request(
            user_id=current_user.username,
            model_id=payload.model_id,
            prompt_hash=hash_prompt(payload.prompt),
            security_score=security_score,
            decision=decision,
            latency_ms=latency_ms,
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
    await log_request(
        user_id=current_user.username,
        model_id=payload.model_id,
        prompt_hash=hash_prompt(payload.prompt),
        security_score=security_score,
        decision=decision,
        latency_ms=latency_ms,
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