from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.policy_engine import evaluate_request
from app.core.rate_limiter import get_penalty_profile, get_request_rate_score
from app.core.security import require_active_user, require_admin
from app.core.trust_score import get_behavior_context
from app.models.model import Model
from app.schemas import (
    DetectRequest,
    DetectionRuleCreate,
    DetectionRuleOut,
    DetectionRuleUpdate,
    RequestDecision,
    SecurityControlCreate,
    SecurityControlOut,
    SecurityControlUpdate,
    TokenData,
)
from app.services.model_registry import get_model_risk_score, get_model_sensitivity_score
from app.services.prompt_guard import GuardDecision, evaluate_prompt_guard
from app.services.reassessment_service import get_user_trust_penalty_persistent
from app.services.security_catalog import (
    build_control_plane,
    create_detection_rule,
    create_security_control,
    disable_detection_rule,
    disable_security_control,
    list_detection_rules,
    list_security_controls,
    update_detection_rule,
    update_security_control,
)
from app.services.threat_intelligence import get_user_attack_sequence_summary

router = APIRouter()


@router.get("/control-plane")
async def control_plane(
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(require_active_user),
):
    return await build_control_plane(db)


@router.get("/controls", response_model=list[SecurityControlOut])
async def get_controls(
    include_disabled: bool = Query(default=False),
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(require_active_user),
):
    return await list_security_controls(db, include_disabled=include_disabled)


@router.post("/controls", response_model=SecurityControlOut, status_code=status.HTTP_201_CREATED)
async def add_control(
    payload: SecurityControlCreate,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(require_admin),
):
    return await create_security_control(db, payload)


@router.patch("/controls/{control_id}", response_model=SecurityControlOut)
async def patch_control(
    control_id: int,
    payload: SecurityControlUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(require_admin),
):
    row = await update_security_control(db, control_id, payload)
    if row is None:
        raise HTTPException(status_code=404, detail="Security control not found")
    return row


@router.delete("/controls/{control_id}", response_model=SecurityControlOut)
async def remove_control(
    control_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(require_admin),
):
    row = await disable_security_control(db, control_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Security control not found")
    return row


@router.get("/detection-rules", response_model=list[DetectionRuleOut])
async def get_detection_rules(
    target: str | None = Query(default=None, pattern="^(prompt|output)$"),
    include_disabled: bool = Query(default=False),
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(require_active_user),
):
    return await list_detection_rules(db, target=target, include_disabled=include_disabled)


@router.post("/detection-rules", response_model=DetectionRuleOut, status_code=status.HTTP_201_CREATED)
async def add_detection_rule(
    payload: DetectionRuleCreate,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(require_admin),
):
    return await create_detection_rule(db, payload)


@router.patch("/detection-rules/{rule_id}", response_model=DetectionRuleOut)
async def patch_detection_rule(
    rule_id: int,
    payload: DetectionRuleUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(require_admin),
):
    row = await update_detection_rule(db, rule_id, payload)
    if row is None:
        raise HTTPException(status_code=404, detail="Detection rule not found")
    return row


@router.delete("/detection-rules/{rule_id}", response_model=DetectionRuleOut)
async def remove_detection_rule(
    rule_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(require_admin),
):
    row = await disable_detection_rule(db, rule_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Detection rule not found")
    return row


@router.post("/policy/simulate")
async def simulate_policy(
    payload: DetectRequest,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(require_active_user),
):
    model_id = payload.model_id or 1
    model = (await db.execute(select(Model).where(Model.id == model_id))).scalar_one_or_none()
    if model is None:
        model_risk_score = 0.5
        sensitivity_score = 0.5
        model_sensitivity = "medium"
        provider = None
    else:
        model_risk_score = await get_model_risk_score(db=db, model_id=model_id)
        sensitivity_score = await get_model_sensitivity_score(db=db, model_id=model_id)
        model_sensitivity = (
            model.sensitivity_level.value
            if hasattr(model.sensitivity_level, "value")
            else str(model.sensitivity_level or "medium")
        )
        provider = model.provider_name

    username = current_user.username or "unknown"
    trust_penalty = await get_user_trust_penalty_persistent(
        db,
        user_id=current_user.user_id,
        username=username,
    )
    behavior_context = get_behavior_context(username)
    attack_sequence_summary = await get_user_attack_sequence_summary(db, user_id=current_user.user_id)
    prompt_result = await evaluate_prompt_guard(
        payload.prompt,
        user_trust_score=max(0.0, 1.0 - trust_penalty),
        model_sensitivity=model_sensitivity,
        provider=provider,
        dynamic_rules=await list_detection_rules(db, target="prompt"),
    )
    policy = evaluate_request(
        model_risk_score=model_risk_score,
        sensitivity_score=sensitivity_score,
        prompt_risk_score=prompt_result.prompt_risk_score,
        request_rate_score=get_request_rate_score(username),
        user_trust_penalty=trust_penalty,
        secure_mode_enabled=bool(getattr(model, "secure_mode_enabled", False)),
        recent_risky_events=behavior_context.get("recent_risky_events", 0),
        recent_blocks=behavior_context.get("recent_blocks", 0),
        recent_challenges=behavior_context.get("recent_challenges", 0),
        model_base_risk_score=getattr(model, "base_risk_score", None),
        secured_model_risk_score=getattr(model, "secured_risk_score", None),
        attack_sequence_severity=attack_sequence_summary.get("sequence_severity", 0.0),
        repeated_pattern_count=attack_sequence_summary.get("repeated_pattern_count", 0),
        cross_model_abuse_score=attack_sequence_summary.get("cross_model_abuse_score", 0.0),
    )

    decision = policy["decision"]
    if prompt_result.decision == GuardDecision.BLOCK:
        decision = RequestDecision.BLOCK
    elif prompt_result.decision == GuardDecision.CHALLENGE and decision == RequestDecision.ALLOW:
        decision = RequestDecision.CHALLENGE

    return {
        "model_id": model_id,
        "decision": decision,
        "prompt_guard": {
            "decision": prompt_result.decision,
            "risk_score": prompt_result.prompt_risk_score,
            "flags": prompt_result.flags,
            "reason": prompt_result.reason,
            "dynamic_rule_matches": prompt_result.dynamic_rule_matches,
        },
        "policy": policy,
        "behavior_context": behavior_context,
        "attack_sequence_summary": attack_sequence_summary,
        "cross_model_abuse": {
            "score": attack_sequence_summary.get("cross_model_abuse_score", 0.0),
            "models": attack_sequence_summary.get("cross_model_models", 0),
            "risky_events": attack_sequence_summary.get("cross_model_risky_events", 0),
        },
        "enforcement_profile": get_penalty_profile(username),
    }
