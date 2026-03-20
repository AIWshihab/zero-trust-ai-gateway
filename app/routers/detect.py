import time
from fastapi import APIRouter, Depends, HTTPException, status

from app.core.security import require_active_user
from app.core.policy_engine import evaluate_request
from app.models.schemas import (
    TokenData,
    DetectRequest,
    DetectResponse,
    InferenceRequest,
    InferenceResponse,
    RequestDecision,
)
from app.models.registry import get_model
from app.services.prompt_guard import analyse_prompt
from app.services.model_router import route_to_model
from app.services.logger import log_request
from app.core.trust_score import get_user_trust_penalty, update_trust_score
from app.core.rate_limiter import get_request_rate_score, record_request
from app.core.security import hash_prompt

router = APIRouter()


# ─── Prompt Detection Only (no inference) ────────────────────────────────────

@router.post("/", response_model=DetectResponse)
async def detect_prompt(
    payload: DetectRequest,
    current_user: TokenData = Depends(require_active_user),
):
    """
    Analyses a prompt for risk without routing to a model.
    Used by the frontend to pre-screen user input.
    """
    prompt_result = analyse_prompt(payload.prompt)

    policy = evaluate_request(
        model_id=payload.model_id or 1,
        prompt_risk_score=prompt_result["risk_score"],
        request_rate_score=get_request_rate_score(current_user.username),
        user_trust_penalty=get_user_trust_penalty(current_user.username),
    )

    return DetectResponse(
        prompt_risk_score=prompt_result["risk_score"],
        flags=prompt_result["flags"],
        decision=policy["decision"],
        reason=policy["reason"],
    )


# ─── Full Inference Request (detect + route to model) ────────────────────────
from app.core.config import get_settings
settings = get_settings()


# ─── Full Inference Request ───────────────────────────────────────────────────

@router.post("/infer", response_model=InferenceResponse)
async def infer(
    payload: InferenceRequest,
    current_user: TokenData = Depends(require_active_user),
):
    start_time = time.time()

    # ── Step 1: Validate model ─────────────────────────────────────────────
    model = get_model(payload.model_id)
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
        # ZTA OFF — bypass all security checks, route directly
        output     = await route_to_model(model, payload.prompt, payload.parameters)
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
    prompt_result  = analyse_prompt(payload.prompt)
    rate_score     = get_request_rate_score(current_user.username)
    trust_penalty  = get_user_trust_penalty(current_user.username)

    policy         = evaluate_request(
        model_id=payload.model_id,
        prompt_risk_score=prompt_result["risk_score"],
        request_rate_score=rate_score,
        user_trust_penalty=trust_penalty,
    )

    decision       = policy["decision"]
    security_score = policy["security_score"]
    reason         = policy["reason"]

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
    output     = await route_to_model(model, payload.prompt, payload.parameters)
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
