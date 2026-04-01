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
    is_rate_limited,
)
from app.core.security import require_active_user, hash_prompt
from app.core.trust_score import (
    get_user_trust_penalty,
    update_trust_score,
)
from app.models.model import Model
from app.models.schemas import (
    InferenceRequest,
    SafeInferenceResponse,
    RequestDecision,
    TokenData,
)
from app.services.logger import log_request
from app.services.model_router import route_to_model
from app.services.prompt_guard import evaluate_prompt_guard, GuardDecision

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


@router.post("/infer", response_model=SafeInferenceResponse)
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

    model_sensitivity = (
        model_row.sensitivity_level.value
        if hasattr(model_row.sensitivity_level, "value")
        else str(model_row.sensitivity_level or "medium")
    )

    # Hard rate limit fast-path
    if is_rate_limited(username):
        latency_ms = (time.perf_counter() - started) * 1000.0
        decision = RequestDecision.BLOCK
        reason = "Blocked by hard rate limit."

        update_trust_score(username, decision)

        await log_request(
            user_id=username,
            model_id=model_row.id,
            prompt_hash=hash_prompt(payload.prompt),
            security_score=1.0,
            decision=decision,
            latency_ms=latency_ms,
            prompt_risk_score=0.0,
            output_risk_score=0.0,
            blocked=True,
            secure_mode_enabled=bool(model_row.secure_mode_enabled),
            reason=reason,
        )

        return SafeInferenceResponse(
            model_id=model_row.id,
            output=None,
            decision=decision,
            prompt_risk_score=0.0,
            output_risk_score=0.0,
            blocked=True,
            reason=reason,
            latency_ms=latency_ms,
            secure_mode_enabled=bool(model_row.secure_mode_enabled),
        )

    # Record request for sliding-window rate score
    record_request(username)
    request_rate_score = get_request_rate_score(username)
    user_trust_penalty = get_user_trust_penalty(username)

    guard_result = await evaluate_prompt_guard(
        payload.prompt,
        user_trust_score=max(0.0, 1.0 - user_trust_penalty),
        model_sensitivity=model_sensitivity,
        provider=model_row.provider_name,
    )

    prompt_risk_score = float(guard_result.prompt_risk_score)

    model_risk_score = 0.5
    if model_row.base_trust_score is not None:
        model_risk_score = max(
            0.0,
            min(1.0, 1.0 - (float(model_row.base_trust_score) / 100.0)),
        )

    policy_result = evaluate_request(
        model_risk_score=model_risk_score,
        sensitivity_score=_sensitivity_to_score(model_row.sensitivity_level),
        prompt_risk_score=prompt_risk_score,
        request_rate_score=request_rate_score,
        user_trust_penalty=user_trust_penalty,
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

    if final_decision == RequestDecision.BLOCK:
        latency_ms = (time.perf_counter() - started) * 1000.0

        update_trust_score(username, final_decision)

        await log_request(
            user_id=username,
            model_id=model_row.id,
            prompt_hash=hash_prompt(payload.prompt),
            security_score=security_score,
            decision=final_decision,
            latency_ms=latency_ms,
            prompt_risk_score=prompt_risk_score,
            output_risk_score=0.0,
            blocked=True,
            secure_mode_enabled=bool(model_row.secure_mode_enabled),
            reason=final_reason,
        )

        return SafeInferenceResponse(
            model_id=model_row.id,
            output=None,
            decision=final_decision,
            prompt_risk_score=prompt_risk_score,
            output_risk_score=0.0,
            blocked=True,
            reason=final_reason,
            latency_ms=latency_ms,
            secure_mode_enabled=bool(model_row.secure_mode_enabled),
        )

    try:
        output_text = await route_to_model(
            model=model_row,
            prompt=payload.prompt,
            parameters=payload.parameters,
        )
    except HTTPException as exc:
        latency_ms = (time.perf_counter() - started) * 1000.0

        update_trust_score(username, RequestDecision.BLOCK)

        await log_request(
            user_id=username,
            model_id=model_row.id,
            prompt_hash=hash_prompt(payload.prompt),
            security_score=max(security_score, prompt_risk_score),
            decision=RequestDecision.BLOCK,
            latency_ms=latency_ms,
            prompt_risk_score=prompt_risk_score,
            output_risk_score=0.0,
            blocked=True,
            secure_mode_enabled=bool(model_row.secure_mode_enabled),
            reason=f"Upstream error: {exc.detail}",
        )
        raise
    except Exception as exc:
        latency_ms = (time.perf_counter() - started) * 1000.0

        update_trust_score(username, RequestDecision.BLOCK)

        await log_request(
            user_id=username,
            model_id=model_row.id,
            prompt_hash=hash_prompt(payload.prompt),
            security_score=max(security_score, prompt_risk_score),
            decision=RequestDecision.BLOCK,
            latency_ms=latency_ms,
            prompt_risk_score=prompt_risk_score,
            output_risk_score=0.0,
            blocked=True,
            secure_mode_enabled=bool(model_row.secure_mode_enabled),
            reason=f"Inference failed: {exc}",
        )
        raise HTTPException(status_code=500, detail=f"Inference failed: {exc}")

    output_guard_result = inspect_output(output_text)
    output_action = output_guard_result.get("action", "allow")
    output_risk_score = float(output_guard_result.get("risk_score", 0.0))
    output_findings = output_guard_result.get("findings", [])

    final_output = output_text
    blocked = False

    if bool(model_row.secure_mode_enabled):
        if output_action == "block":
            final_output = None
            blocked = True
            final_decision = RequestDecision.BLOCK
            final_reason = "Blocked by output guard."
        elif output_action == "redact":
            final_output = "[REDACTED BY OUTPUT GUARD]"
            final_reason = "Response redacted by output guard."

    if output_findings:
        final_reason = f"{final_reason} " + "; ".join(output_findings)

    latency_ms = (time.perf_counter() - started) * 1000.0
    combined_security_score = max(
        security_score,
        prompt_risk_score,
        min(1.0, output_risk_score / 100.0),
    )

    update_trust_score(username, final_decision)

    await log_request(
        user_id=username,
        model_id=model_row.id,
        prompt_hash=hash_prompt(payload.prompt),
        security_score=combined_security_score,
        decision=final_decision,
        latency_ms=latency_ms,
        prompt_risk_score=prompt_risk_score,
        output_risk_score=output_risk_score,
        blocked=blocked,
        secure_mode_enabled=bool(model_row.secure_mode_enabled),
        reason=final_reason,
    )

    return SafeInferenceResponse(
        model_id=model_row.id,
        output=final_output,
        decision=final_decision,
        prompt_risk_score=prompt_risk_score,
        output_risk_score=output_risk_score,
        blocked=blocked,
        reason=final_reason,
        latency_ms=latency_ms,
        secure_mode_enabled=bool(model_row.secure_mode_enabled),
    )