import json
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import get_db
from app.core.protection_engine import compute_protected_score
from app.core.security import require_admin, require_active_user
from app.models.model import Model
from app.schemas import ErrorResponse, ProtectionConfig, ProtectionScoreResponse, ScanStatus, TokenData
from app.services.model_readiness import ensure_model_ready
from app.services.model_posture_engine import build_control_context, compute_secured_risk_from_controls
from app.services.reassessment_service import reassess_model_posture

router = APIRouter()


def _extract_protection_config_from_summary(scan_summary_json: str | None) -> dict[str, Any]:
    if not scan_summary_json:
        return {}

    try:
        parsed = json.loads(scan_summary_json)
    except Exception:
        return {}

    if not isinstance(parsed, dict):
        return {}

    protection = parsed.get("protection")
    if not isinstance(protection, dict):
        return {}

    config = protection.get("config")
    if not isinstance(config, dict):
        return {}

    return config


def _safe_float(value) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except Exception:
        return None


def _recompute_secured_risk_context(
    *,
    model_row: Model,
    protection_config: dict[str, Any] | None,
    secure_mode_enabled: bool,
) -> None:
    base_risk_score = _safe_float(model_row.base_risk_score)
    if base_risk_score is None:
        return

    control_context = build_control_context(
        settings=get_settings(),
        secure_mode_enabled=secure_mode_enabled,
        protection_config=protection_config,
    )
    secured_risk = compute_secured_risk_from_controls(
        base_risk_score=base_risk_score,
        control_context=control_context,
    )

    model_row.secured_risk_score = float(secured_risk["secured_risk_score"])
    model_row.risk_reduction_pct = float(secured_risk["risk_reduction_pct"])
    model_row.last_reassessed_at = datetime.now(timezone.utc)

    posture_factors = model_row.posture_factors or {}
    posture_factors["secured_risk_controls"] = secured_risk["secured_risk_controls"]
    posture_factors["secure_mode_context"] = {
        "secure_mode_enabled": bool(secure_mode_enabled),
        "reassessed_at": model_row.last_reassessed_at.isoformat(),
        "reassessment_reason": "Protection mode changed and effective controls were recalculated.",
        "control_context": control_context,
    }
    model_row.posture_factors = posture_factors

    existing_explanations = model_row.posture_explanations or []
    active_mode_text = "enabled" if secure_mode_enabled else "disabled"
    reassessment_line = (
        f"Secure mode {active_mode_text}: secured risk recalculated to "
        f"{model_row.secured_risk_score}/100 with reduction {model_row.risk_reduction_pct}%."
    )

    merged_explanations = [line for line in existing_explanations if isinstance(line, str)]
    merged_explanations.append(reassessment_line)
    merged_explanations.extend(
        [line for line in secured_risk["risk_reduction_explanations"] if isinstance(line, str)]
    )

    # Keep the payload bounded for UI/API stability.
    model_row.posture_explanations = merged_explanations[-25:]


@router.post(
    "/{model_id}/enable",
    response_model=ProtectionScoreResponse,
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Admin access required"},
        409: {"model": ErrorResponse, "description": "Model not ready"},
        404: {"model": ErrorResponse, "description": "Model not found"},
    },
)
async def enable_protection(
    model_id: int,
    payload: ProtectionConfig,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(require_admin),
):
    result = await db.execute(select(Model).where(Model.id == model_id))
    model_row = result.scalar_one_or_none()

    if not model_row:
        raise HTTPException(status_code=404, detail="Model not found")

    ensure_model_ready(model_row, action="protection enable")

    protection_result = compute_protected_score(
        base_trust_score=float(model_row.base_trust_score),
        require_auth=payload.require_auth,
        prompt_filtering=payload.prompt_filtering,
        output_filtering=payload.output_filtering,
        logging_enabled=payload.logging_enabled,
        anomaly_detection=payload.anomaly_detection,
        rate_limit_enabled=payload.rate_limit_enabled,
    )

    model_row.protected_score = protection_result["protected_score"]
    model_row.secure_mode_enabled = True
    model_row.scan_status = ScanStatus.PROTECTED.value

    existing_summary = {}
    if model_row.scan_summary_json:
        try:
            existing_summary = json.loads(model_row.scan_summary_json)
        except Exception:
            existing_summary = {}

    existing_summary["protection"] = {
        "config": payload.model_dump(),
        "result": protection_result,
    }
    model_row.scan_summary_json = json.dumps(existing_summary)
    _recompute_secured_risk_context(
        model_row=model_row,
        protection_config=payload.model_dump(),
        secure_mode_enabled=True,
    )
    await reassess_model_posture(
        db,
        model_row=model_row,
        trigger="protection_mode_change",
        request_context={
            "decision": "allow",
            "secure_mode_enabled": True,
            "request_rate_score": 0.0,
        },
        commit=False,
    )

    await db.commit()
    await db.refresh(model_row)

    return ProtectionScoreResponse(
        model_id=model_row.id,
        secure_mode_enabled=bool(model_row.secure_mode_enabled),
        base_trust_score=float(protection_result["base_trust_score"]),
        protected_score=float(protection_result["protected_score"]),
        improvement_delta=float(protection_result["improvement_delta"]),
        active_controls=protection_result["active_controls"],
    )


@router.post(
    "/{model_id}/disable",
    response_model=ProtectionScoreResponse,
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Admin access required"},
        409: {"model": ErrorResponse, "description": "Model not ready"},
        404: {"model": ErrorResponse, "description": "Model not found"},
    },
)
async def disable_protection(
    model_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(require_admin),
):
    result = await db.execute(select(Model).where(Model.id == model_id))
    model_row = result.scalar_one_or_none()

    if not model_row:
        raise HTTPException(status_code=404, detail="Model not found")

    ensure_model_ready(model_row, action="protection disable")

    model_row.secure_mode_enabled = False
    model_row.protected_score = model_row.base_trust_score
    model_row.scan_status = ScanStatus.COMPLETED.value
    _recompute_secured_risk_context(
        model_row=model_row,
        protection_config=_extract_protection_config_from_summary(model_row.scan_summary_json),
        secure_mode_enabled=False,
    )
    await reassess_model_posture(
        db,
        model_row=model_row,
        trigger="protection_mode_change",
        request_context={
            "decision": "allow",
            "secure_mode_enabled": False,
            "request_rate_score": 0.0,
        },
        commit=False,
    )

    await db.commit()
    await db.refresh(model_row)

    return ProtectionScoreResponse(
        model_id=model_row.id,
        secure_mode_enabled=False,
        base_trust_score=float(model_row.base_trust_score),
        protected_score=float(model_row.protected_score),
        improvement_delta=max(
            0.0,
            float(model_row.protected_score) - float(model_row.base_trust_score),
        ),
        active_controls=[],
    )


@router.get(
    "/{model_id}/score",
    response_model=ProtectionScoreResponse,
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        409: {"model": ErrorResponse, "description": "Model not ready"},
        404: {"model": ErrorResponse, "description": "Model not found"},
    },
)
async def get_protection_score(
    model_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(require_active_user),
):
    result = await db.execute(select(Model).where(Model.id == model_id))
    model_row = result.scalar_one_or_none()

    if not model_row:
        raise HTTPException(status_code=404, detail="Model not found")

    ensure_model_ready(model_row, action="protection score")

    protected_score = (
        float(model_row.protected_score)
        if model_row.protected_score is not None
        else float(model_row.base_trust_score)
    )

    return ProtectionScoreResponse(
        model_id=model_row.id,
        secure_mode_enabled=bool(model_row.secure_mode_enabled),
        base_trust_score=float(model_row.base_trust_score),
        protected_score=protected_score,
        improvement_delta=max(0.0, protected_score - float(model_row.base_trust_score)),
        active_controls=[],
    )
