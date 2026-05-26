from uuid import uuid4

import hmac

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.config import get_settings
from app.models.model import Model
from app.routers.usage import safe_infer
from app.schemas import (
    GatewayInterceptRequest,
    GatewayInterceptResponse,
    InferenceRequest,
    OpenAIChatCompletionRequest,
    OpenAIChatCompletionResponse,
    RequestDecision,
    SafeInferenceResponse,
    TokenData,
)
from app.schemas.gateway import (
    BrowserCheckRequest,
    BrowserCheckResponse,
    OpenAIChatCompletionChoice,
    OpenAIChatCompletionMessage,
)
from app.core.security import require_active_user, hash_prompt
from app.services.firewall_clients import authenticate_firewall_client

router = APIRouter()


async def require_gateway_api_key(
    x_gateway_api_key: str | None = Header(default=None),
    db: AsyncSession = Depends(get_db),
) -> str:
    if not x_gateway_api_key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing gateway API key")

    configured = [
        key.strip()
        for key in (get_settings().GATEWAY_API_KEYS or "").split(",")
        if key.strip()
    ]
    if any(hmac.compare_digest(x_gateway_api_key, key) for key in configured):
        return x_gateway_api_key

    try:
        await authenticate_firewall_client(db, x_gateway_api_key)
        return x_gateway_api_key
    except HTTPException as exc:
        if exc.status_code != status.HTTP_403_FORBIDDEN:
            raise
    except Exception:
        if hasattr(db, "execute"):
            raise
        pass

    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid gateway API key")


def _messages_to_prompt(messages: list[dict]) -> str:
    if not messages:
        return ""

    last_content = None
    for message in reversed(messages):
        content = message.get("content") if isinstance(message, dict) else None
        if isinstance(content, str) and content.strip():
            last_content = content
            break
        if isinstance(content, list):
            text_parts = [
                str(part.get("text", ""))
                for part in content
                if isinstance(part, dict) and part.get("type") in {None, "text"}
            ]
            combined = "\n".join(part for part in text_parts if part.strip())
            if combined:
                last_content = combined
                break

    return (last_content or "").strip()


async def _resolve_model_id(db: AsyncSession, model_ref: str) -> int:
    try:
        model_id = int(model_ref)
        if model_id > 0:
            return model_id
    except (TypeError, ValueError):
        pass

    normalized = str(model_ref or "").strip()
    if not normalized:
        raise HTTPException(status_code=422, detail="model_id is required")

    result = await db.execute(
        select(Model.id).where(
            or_(
                Model.name == normalized,
                Model.hf_model_id == normalized,
                Model.provider_name == normalized,
            )
        )
    )
    model_id = result.scalar_one_or_none()
    if model_id is None:
        raise HTTPException(status_code=404, detail="Model mapping not found")
    return int(model_id)


def _gateway_user(*, external_user_id: str | None, client_id: str | None) -> TokenData:
    username = external_user_id or client_id or "gateway_external"
    return TokenData(user_id=None, username=f"gateway:{username}", scopes=["gateway"])


async def _run_gateway_pipeline(
    *,
    db: AsyncSession,
    model_ref: str,
    prompt: str,
    messages: list[dict],
    external_user_id: str | None,
    client_id: str | None,
    policy_context: dict,
    parameters: dict,
    source: str,
    trace_id: str,
    extra_gateway_context: dict | None = None,
) -> SafeInferenceResponse:
    model_id = await _resolve_model_id(db, model_ref)
    if not prompt.strip():
        raise HTTPException(status_code=422, detail="prompt or messages content is required")

    pipeline_parameters = dict(parameters or {})
    pipeline_parameters["gateway_context"] = {
        "trace_id": trace_id,
        "client_id": client_id,
        "external_user_id": external_user_id,
        "source": source,
        "forwarded": False,
        "policy_context": dict(policy_context or {}),
        **dict(extra_gateway_context or {}),
    }
    if messages:
        pipeline_parameters["messages"] = messages

    return await safe_infer(
        InferenceRequest(
            model_id=model_id,
            prompt=prompt,
            messages=messages,
            parameters=pipeline_parameters,
        ),
        db=db,
        current_user=_gateway_user(external_user_id=external_user_id, client_id=client_id),
    )


@router.post("/gateway/intercept", response_model=GatewayInterceptResponse)
async def intercept_gateway_request(
    payload: GatewayInterceptRequest,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(require_gateway_api_key),
):
    trace_id = f"gateway-{uuid4().hex}"
    prompt = (payload.prompt or _messages_to_prompt(payload.messages)).strip()
    result = await _run_gateway_pipeline(
        db=db,
        model_ref=payload.model_id,
        prompt=prompt,
        messages=payload.messages,
        external_user_id=payload.external_user_id,
        client_id=payload.client_id,
        policy_context=payload.policy_context,
        parameters=payload.parameters,
        source="gateway_intercept",
        trace_id=trace_id,
    )

    return GatewayInterceptResponse(
        decision=result.decision,
        output=result.output,
        reason=result.reason,
        effective_risk=result.effective_risk,
        trace_id=trace_id,
        forwarded=bool(result.forwarded),
        factors=result.factors,
        explanation=result.explanation,
        decision_trace=result.decision_trace,
    )


@router.post("/proxy/openai/chat/completions")
async def proxy_openai_chat_completions(
    payload: OpenAIChatCompletionRequest,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(require_gateway_api_key),
):
    trace_id = f"gateway-{uuid4().hex}"
    parameters = {}
    if payload.temperature is not None:
        parameters["temperature"] = payload.temperature
    if payload.max_tokens is not None:
        parameters["max_tokens"] = payload.max_tokens

    result = await _run_gateway_pipeline(
        db=db,
        model_ref=payload.model,
        prompt=_messages_to_prompt(payload.messages),
        messages=payload.messages,
        external_user_id=None,
        client_id="openai-proxy",
        policy_context={},
        parameters=parameters,
        source="openai_proxy",
        trace_id=trace_id,
    )

    if result.decision != RequestDecision.ALLOW:
        return {
            "error": {
                "type": "security_block",
                "message": result.reason or "Blocked by gateway policy.",
                "risk": result.effective_risk,
            }
        }

    return OpenAIChatCompletionResponse(
        id=trace_id,
        choices=[
            OpenAIChatCompletionChoice(
                message=OpenAIChatCompletionMessage(
                    role="assistant",
                    content=result.output or "",
                )
            )
        ],
    )


@router.post("/gateway/check", response_model=BrowserCheckResponse)
async def browser_request_check(
    payload: BrowserCheckRequest,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(require_active_user),
):
    """Lightweight Zero Trust policy check for browser extension request interception.
    Runs prompt guard + policy evaluation without calling any AI model.
    Called by the browser extension before allowing requests to external AI APIs.
    """
    import time as _time
    from app.core.policy_engine import evaluate_request
    from app.core.rate_limiter import get_request_rate_score
    from app.services.prompt_guard import evaluate_prompt_guard
    from app.services.reassessment_service import get_user_trust_penalty_persistent
    from app.services.security_catalog import list_detection_rules
    from app.services.db_logger import log_request_db

    prompt = (payload.extracted_prompt or "").strip()

    # No prompt content → allow (nothing to evaluate)
    if not prompt:
        return BrowserCheckResponse(decision="allow", reason="No prompt content", risk_score=0.0)

    t0 = _time.monotonic()

    user_trust = await get_user_trust_penalty_persistent(
        db, current_user.user_id, current_user.username
    )
    dynamic_rules = await list_detection_rules(db, target="prompt")
    rate_score = get_request_rate_score(current_user.username)

    guard = await evaluate_prompt_guard(
        prompt,
        user_trust_score=user_trust,
        dynamic_rules=dynamic_rules,
    )

    policy = evaluate_request(
        model_risk_score=0.4,
        sensitivity_score=0.4,
        prompt_risk_score=guard.risk_score,
        request_rate_score=rate_score,
        user_trust_penalty=user_trust,
    )

    if guard.decision.value == "block" or policy.get("decision") == "block":
        decision = "block"
    elif guard.decision.value == "challenge" or policy.get("decision") == "challenge":
        decision = "challenge"
    else:
        decision = "allow"

    reason  = guard.reason or policy.get("reason") or ""
    risk    = float(guard.prompt_risk_score or policy.get("security_score") or 0.0)
    latency = (_time.monotonic() - t0) * 1000

    # Log browser-intercept requests only when a real model_id is resolvable
    try:
        from sqlalchemy import select as _select
        from app.models.model import Model as _Model
        first_model = (await db.execute(_select(_Model.id).limit(1))).scalar_one_or_none()
        if first_model is not None:
            await log_request_db(
                db,
                user_id=current_user.user_id,
                model_id=int(first_model),
                prompt_hash=hash_prompt(prompt),
                security_score=float(policy.get("security_score", risk)),
                decision=RequestDecision(decision),
                latency_ms=latency,
                prompt_risk_score=risk,
                reason=reason,
                decision_input_snapshot={"target_url": payload.target_url, "source": payload.source},
                decision_trace={"guard_flags": guard.flags, "policy_factors": policy.get("factors", {})},
            )
    except Exception:
        pass  # logging is best-effort for browser intercepts

    factors = list(
        set((guard.flags or []) + list((policy.get("factors") or {}).keys()))
    )[:10]

    return BrowserCheckResponse(
        decision=decision,
        reason=reason or None,
        risk_score=round(risk, 4),
        factors=factors,
    )
