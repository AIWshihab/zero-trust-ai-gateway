import json
import time
from datetime import datetime, timezone
from typing import Any, AsyncIterator

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.data_sensitivity import classify_data_sensitivity
from app.core.output_guard import inspect_output
from app.core.policy_engine import evaluate_request
from app.core.rate_limiter import (
    get_penalty_profile,
    get_request_rate_score,
    is_rate_limited,
    record_abuse_outcome,
    record_request,
)
from app.core.security import hash_prompt, require_active_user
from app.core.trust_score import get_behavior_context, record_behavior_event
from app.models.model import Model
from app.models.chat import ChatMessage, ChatSession
from app.schemas import RequestDecision, TokenData
from app.services.db_logger import log_request_db
from app.services.explainability import build_decision_explanation
from app.services.model_readiness import ensure_model_ready
from app.services.model_router import route_to_model, stream_route_to_model, _WARMING_SENTINEL
from app.services.model_runtime import ensure_model_runtime_ready
from app.services.prompt_guard import evaluate_prompt_guard
from app.services.reassessment_service import (
    get_user_trust_penalty_persistent,
    reassess_model_posture,
    reassess_user_trust_on_request,
)
from app.services.security_catalog import list_detection_rules
from app.services.threat_intelligence import (
    get_user_attack_sequence_summary,
    update_attack_sequence,
)
from app.routers.usage import (
    _sensitivity_to_score,
    _guard_to_request_decision,
    _model_base_risk_score,
    _model_secured_risk_score,
    _can_use_model,
    _decision_snapshot,
    _gateway_context,
    _with_gateway_context,
    _chat_detail_from_http_exception,
)

router = APIRouter()


class StreamInferenceRequest(BaseModel):
    model_id: int = Field(..., gt=0)
    prompt: str = Field(..., min_length=1, max_length=4096)
    messages: list[dict[str, str]] = Field(default_factory=list)
    parameters: dict[str, Any] = Field(default_factory=dict)
    session_id: int | None = Field(default=None, gt=0)


def _sse(data: dict) -> str:
    return f"data: {json.dumps(data)}\n\n"


@router.post("/stream-infer")
async def stream_infer(
    payload: StreamInferenceRequest,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(require_active_user),
):
    async def gen() -> AsyncIterator[str]:
        started = time.perf_counter()
        username = current_user.username
        gw_ctx = _gateway_context(payload)
        chat_session: ChatSession | None = None
        user_message_saved = False

        def _err(code: str, msg: str) -> str:
            return _sse({"type": "error", "code": code, "message": msg})

        async def persist_message(
            *,
            role: str,
            content: str,
            decision_payload: dict | None = None,
        ) -> None:
            nonlocal user_message_saved
            if chat_session is None:
                return
            decision_payload = decision_payload or {}
            message = ChatMessage(
                session_id=chat_session.id,
                user_id=current_user.user_id,
                model_id=payload.model_id,
                role=role,
                content=content or "",
                decision=decision_payload.get("decision"),
                prompt_risk_score=decision_payload.get("prompt_risk_score"),
                security_score=decision_payload.get("security_score"),
                effective_risk=decision_payload.get("effective_risk"),
                blocked=decision_payload.get("blocked"),
                gateway_trace=decision_payload or None,
            )
            db.add(message)
            if role == "user":
                user_message_saved = True
                if chat_session.title == "New chat":
                    chat_session.title = (content or "New chat")[:80]
            chat_session.model_id = payload.model_id
            chat_session.updated_at = datetime.now(timezone.utc)
            await db.commit()

        result = await db.execute(select(Model).where(Model.id == payload.model_id))
        model_row = result.scalar_one_or_none()

        if payload.session_id is not None:
            chat_session = (
                await db.execute(
                    select(ChatSession).where(
                        ChatSession.id == payload.session_id,
                        ChatSession.user_id == current_user.user_id,
                    )
                )
            ).scalar_one_or_none()
            if chat_session is None:
                yield _err("chat_session_not_found", "Chat session not found.")
                yield _sse({"type": "done", "latency_ms": 0, "blocked": False})
                return

        if not model_row:
            yield _err("model_not_found", "Model not found.")
            yield _sse({"type": "done", "latency_ms": 0, "blocked": False})
            return

        if not _can_use_model(model_row, current_user):
            yield _err("forbidden", "You can only run inference on global models or models owned by your account.")
            yield _sse({"type": "done", "latency_ms": 0, "blocked": False})
            return

        if not bool(model_row.is_active):
            yield _err("model_inactive", "This model is inactive in the registry.")
            yield _sse({"type": "done", "latency_ms": 0, "blocked": False})
            return

        if chat_session is not None and not user_message_saved:
            await persist_message(role="user", content=payload.prompt)

        model_sensitivity = (
            model_row.sensitivity_level.value
            if hasattr(model_row.sensitivity_level, "value")
            else str(model_row.sensitivity_level or "medium")
        )
        secure_mode_enabled = bool(model_row.secure_mode_enabled)

        await reassess_model_posture(
            db, model_row=model_row, trigger="request_precheck",
            request_context={"decision": "allow", "secure_mode_enabled": secure_mode_enabled},
            commit=False,
        )

        penalty_profile = get_penalty_profile(username)
        if penalty_profile.get("penalty_active"):
            remaining = int(penalty_profile.get("cooldown_remaining_seconds") or 0)
            reason = f"Temporary abuse penalty active. Retry after {remaining} second(s)."
            yield _sse({
                "type": "decision", "decision": "BLOCK", "blocked": True,
                "prompt_risk_score": 1.0, "security_score": 1.0, "effective_risk": 1.0,
                "reason": reason, "explanation": reason, "factors": {},
                "secure_mode_enabled": secure_mode_enabled, "decision_trace": {},
            })
            yield _sse({"type": "done", "latency_ms": (time.perf_counter() - started) * 1000, "blocked": True})
            return

        if is_rate_limited(username):
            reason = "Blocked by hard rate limit."
            yield _sse({
                "type": "decision", "decision": "BLOCK", "blocked": True,
                "prompt_risk_score": 0.0, "security_score": 1.0, "effective_risk": 1.0,
                "reason": reason, "explanation": reason, "factors": {},
                "secure_mode_enabled": secure_mode_enabled, "decision_trace": {},
            })
            yield _sse({"type": "done", "latency_ms": (time.perf_counter() - started) * 1000, "blocked": True})
            return

        record_request(username)
        request_rate_score = get_request_rate_score(username)
        user_trust_penalty = await get_user_trust_penalty_persistent(
            db, user_id=current_user.user_id, username=username,
        )
        behavior_context = get_behavior_context(username)
        attack_sequence_summary = await get_user_attack_sequence_summary(db, user_id=current_user.user_id)

        guard_result = await evaluate_prompt_guard(
            payload.prompt,
            user_trust_score=max(0.0, 1.0 - user_trust_penalty),
            model_sensitivity=model_sensitivity,
            provider=model_row.provider_name,
            dynamic_rules=await list_detection_rules(db, target="prompt"),
        )

        prompt_risk_score = float(guard_result.prompt_risk_score)
        data_sensitivity = classify_data_sensitivity(payload.prompt)

        model_base_risk_score = _model_base_risk_score(model_row)
        secured_model_risk_score = _model_secured_risk_score(model_row)
        model_risk_score = 0.5
        if model_base_risk_score is not None:
            model_risk_score = max(0.0, min(1.0, model_base_risk_score / 100.0))
        elif model_row.base_trust_score is not None:
            model_risk_score = max(0.0, min(1.0, 1.0 - (float(model_row.base_trust_score) / 100.0)))

        policy_result = evaluate_request(
            model_risk_score=model_risk_score,
            sensitivity_score=max(_sensitivity_to_score(model_row.sensitivity_level), data_sensitivity.score),
            prompt_risk_score=prompt_risk_score,
            request_rate_score=request_rate_score,
            user_trust_penalty=user_trust_penalty,
            secure_mode_enabled=secure_mode_enabled,
            recent_risky_events=behavior_context.get("recent_risky_events", 0),
            recent_blocks=behavior_context.get("recent_blocks", 0),
            recent_challenges=behavior_context.get("recent_challenges", 0),
            model_base_risk_score=model_base_risk_score,
            secured_model_risk_score=secured_model_risk_score,
            attack_sequence_severity=attack_sequence_summary.get("sequence_severity", 0.0),
            repeated_pattern_count=attack_sequence_summary.get("repeated_pattern_count", 0),
            cross_model_abuse_score=attack_sequence_summary.get("cross_model_abuse_score", 0.0),
        )

        policy_decision = policy_result.get("decision", RequestDecision.ALLOW)
        policy_reason = policy_result.get("reason", "Policy evaluation completed")
        security_score = float(policy_result.get("security_score", prompt_risk_score))
        effective_risk = float(policy_result.get("effective_risk", security_score))

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
            attack_sequence_summary=attack_sequence_summary,
        )
        decision_input_snapshot["data_sensitivity"] = {
            "level": data_sensitivity.level,
            "score": data_sensitivity.score,
            "findings": data_sensitivity.findings,
        }
        decision_trace["data_sensitivity"] = decision_input_snapshot["data_sensitivity"]

        # Emit decision immediately — frontend shows badge before model call
        yield _sse({
            "type": "decision",
            "decision": final_decision.value,
            "blocked": final_decision == RequestDecision.BLOCK,
            "prompt_risk_score": prompt_risk_score,
            "security_score": security_score,
            "effective_risk": effective_risk,
            "reason": final_reason,
            "explanation": policy_result.get("explanation", final_reason),
            "factors": {
                "prompt_risk": prompt_risk_score,
                "user_trust": user_trust_penalty,
                "model_risk": model_risk_score,
                "sensitivity": _sensitivity_to_score(model_row.sensitivity_level),
            },
            "secure_mode_enabled": secure_mode_enabled,
            "decision_trace": decision_trace,
        })

        if final_decision == RequestDecision.BLOCK:
            penalty_profile = record_abuse_outcome(
                username, decision=final_decision.value,
                prompt_risk_score=prompt_risk_score, security_score=security_score, reason=final_reason,
            )
            trust_update = await reassess_user_trust_on_request(
                db, user_id=current_user.user_id, username=username,
                decision=final_decision, prompt_risk_score=prompt_risk_score,
                security_score=security_score, request_rate_score=request_rate_score,
                secure_mode_enabled=secure_mode_enabled, behavior_context=behavior_context, commit=False,
            )
            record_behavior_event(username, final_decision, prompt_risk_score=prompt_risk_score,
                security_score=security_score, request_rate_score=request_rate_score,
                secure_mode_enabled=secure_mode_enabled)
            await reassess_model_posture(db, model_row=model_row, trigger="request_outcome",
                request_context={"decision": final_decision.value, "request_rate_score": request_rate_score,
                    "prompt_risk_score": prompt_risk_score, "security_score": security_score,
                    "secure_mode_enabled": secure_mode_enabled, "penalty_profile": penalty_profile},
                commit=False)
            await update_attack_sequence(db, user_id=current_user.user_id, model_id=model_row.id,
                event_type="safe_inference_block", decision=final_decision,
                risk_score=prompt_risk_score, security_score=security_score, reason=final_reason,
                flags=list(getattr(guard_result, "flags", [])),
                prompt_hash=hash_prompt(payload.prompt),
                metadata={"policy_adaptive_reasons": policy_result.get("adaptive_reasons", [])},
                commit=False)
            latency_ms = (time.perf_counter() - started) * 1000.0
            await log_request_db(db, user_id=current_user.user_id, model_id=model_row.id,
                prompt_hash=hash_prompt(payload.prompt), security_score=security_score,
                decision=final_decision, latency_ms=latency_ms,
                prompt_risk_score=prompt_risk_score, output_risk_score=0.0,
                blocked=True, secure_mode_enabled=secure_mode_enabled, reason=final_reason,
                decision_input_snapshot=_with_gateway_context(
                    {**decision_input_snapshot, "trust_update": trust_update, "penalty_profile": penalty_profile},
                    gw_ctx, forwarded=False),
                decision_trace=_with_gateway_context(decision_trace, gw_ctx, forwarded=False))
            await persist_message(
                role="system",
                content=final_reason,
                decision_payload={
                    "decision": final_decision.value,
                    "blocked": True,
                    "prompt_risk_score": prompt_risk_score,
                    "security_score": security_score,
                    "effective_risk": effective_risk,
                    "reason": final_reason,
                    "explanation": policy_result.get("explanation", final_reason),
                    "factors": {
                        "prompt_risk": prompt_risk_score,
                        "user_trust": user_trust_penalty,
                        "model_risk": model_risk_score,
                        "sensitivity": _sensitivity_to_score(model_row.sensitivity_level),
                    },
                    "decision_trace": decision_trace,
                },
            )
            yield _sse({"type": "done", "latency_ms": latency_ms, "blocked": True})
            return

        # Model readiness
        try:
            ensure_model_ready(model_row, action="inference")
            ensure_model_runtime_ready(model_row)
        except Exception as exc:
            detail = _chat_detail_from_http_exception(exc) if hasattr(exc, "status_code") else {}
            msg = detail.get("explanation") or detail.get("reason") or str(exc)
            yield _err("model_not_ready", msg)
            yield _sse({"type": "done", "latency_ms": (time.perf_counter() - started) * 1000, "blocked": False})
            return

        # Model inference
        try:
            chunks: list[str] = []
            async for chunk in stream_route_to_model(
                model=model_row,
                prompt=payload.prompt,
                parameters=payload.parameters,
                messages=payload.messages if payload.messages else None,
            ):
                if chunk.startswith(_WARMING_SENTINEL):
                    yield _sse({"type": "warming", "message": chunk[len(_WARMING_SENTINEL):]})
                else:
                    chunks.append(chunk)
                    yield _sse({"type": "content_delta", "text": chunk})
            output_text = "".join(chunks)
            if not output_text:
                output_text = await route_to_model(
                    model=model_row,
                    prompt=payload.prompt,
                    parameters=payload.parameters,
                    messages=payload.messages if payload.messages else None,
                )
        except Exception as exc:
            detail = _chat_detail_from_http_exception(exc) if hasattr(exc, "status_code") else {}
            msg = detail.get("reason") or str(exc) or detail.get("explanation") or "Model provider error"
            await persist_message(role="system", content=msg)
            yield _err("provider_error", msg)
            yield _sse({"type": "done", "latency_ms": (time.perf_counter() - started) * 1000, "blocked": False})
            return

        # Output guard
        output_guard_result = inspect_output(
            output_text,
            dynamic_rules=await list_detection_rules(db, target="output"),
        )
        output_action = output_guard_result.get("action", "allow")
        output_risk_score = float(output_guard_result.get("risk_score", 0.0))
        output_findings = output_guard_result.get("findings", [])

        final_output = output_text
        output_blocked = False

        if secure_mode_enabled:
            if output_action == "block":
                final_output = None
                output_blocked = True
                final_decision = RequestDecision.BLOCK
                final_reason = "Blocked by output guard."
            elif output_action == "redact":
                final_output = output_guard_result.get("redacted_text") or "[REDACTED BY OUTPUT GUARD]"
                final_reason = "Response redacted by output guard."

        if output_findings:
            final_reason = f"{final_reason} " + "; ".join(output_findings)

        latency_ms = (time.perf_counter() - started) * 1000.0
        combined_security_score = max(security_score, prompt_risk_score, min(1.0, output_risk_score / 100.0))

        if output_action in {"block", "redact"}:
            yield _sse({
                "type": "output_guard",
                "action": output_action,
                "text": final_output,
                "blocked": output_blocked,
                "reason": final_reason,
                "findings": output_findings,
            })

        yield _sse({"type": "done", "latency_ms": latency_ms, "blocked": output_blocked})

        # Post-inference accounting runs after streaming completes
        penalty_profile = record_abuse_outcome(
            username, decision=final_decision.value,
            prompt_risk_score=prompt_risk_score,
            security_score=combined_security_score, reason=final_reason,
        )
        trust_update = await reassess_user_trust_on_request(
            db, user_id=current_user.user_id, username=username,
            decision=final_decision, prompt_risk_score=prompt_risk_score,
            security_score=combined_security_score, request_rate_score=request_rate_score,
            secure_mode_enabled=secure_mode_enabled, behavior_context=behavior_context, commit=False,
        )
        record_behavior_event(username, final_decision, prompt_risk_score=prompt_risk_score,
            security_score=combined_security_score, request_rate_score=request_rate_score,
            secure_mode_enabled=secure_mode_enabled)
        await reassess_model_posture(db, model_row=model_row, trigger="request_outcome",
            request_context={"decision": final_decision.value, "request_rate_score": request_rate_score,
                "prompt_risk_score": prompt_risk_score, "security_score": combined_security_score,
                "secure_mode_enabled": secure_mode_enabled, "penalty_profile": penalty_profile},
            commit=False)
        decision_trace["final_decision"] = final_decision.value
        decision_trace["output_guard_action"] = output_action
        decision_trace["output_guard_findings"] = output_findings
        await update_attack_sequence(db, user_id=current_user.user_id, model_id=model_row.id,
            event_type="safe_inference_result", decision=final_decision,
            risk_score=prompt_risk_score, security_score=combined_security_score,
            reason=final_reason, flags=list(getattr(guard_result, "flags", [])),
            prompt_hash=hash_prompt(payload.prompt),
            metadata={"output_guard_action": output_action, "output_guard_findings": output_findings,
                "policy_adaptive_reasons": policy_result.get("adaptive_reasons", [])},
            commit=False)
        await log_request_db(db, user_id=current_user.user_id, model_id=model_row.id,
            prompt_hash=hash_prompt(payload.prompt), security_score=combined_security_score,
            decision=final_decision, latency_ms=latency_ms,
            prompt_risk_score=prompt_risk_score, output_risk_score=output_risk_score,
            blocked=output_blocked, secure_mode_enabled=secure_mode_enabled, reason=final_reason,
            decision_input_snapshot=_with_gateway_context(
                {**decision_input_snapshot, "trust_update": trust_update, "penalty_profile": penalty_profile},
                gw_ctx, forwarded=True),
            decision_trace=_with_gateway_context(decision_trace, gw_ctx, forwarded=True))
        await persist_message(
            role="system" if output_blocked else "assistant",
            content=final_output or final_reason,
            decision_payload={
                "decision": final_decision.value,
                "blocked": output_blocked,
                "prompt_risk_score": prompt_risk_score,
                "security_score": combined_security_score,
                "effective_risk": effective_risk,
                "reason": final_reason,
                "explanation": policy_result.get("explanation", final_reason),
                "factors": {
                    "prompt_risk": prompt_risk_score,
                    "user_trust": user_trust_penalty,
                    "model_risk": model_risk_score,
                    "sensitivity": _sensitivity_to_score(model_row.sensitivity_level),
                },
                "decision_trace": decision_trace,
                "output_guard_action": output_action,
                "output_guard_findings": output_findings,
            },
        )

    return StreamingResponse(
        gen(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
