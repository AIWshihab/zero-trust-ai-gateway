import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.protection_engine import compute_protected_score
from app.models.model import Model
from app.models.schemas import ProtectionConfig, ProtectionScoreResponse

router = APIRouter()


@router.post("/{model_id}/enable", response_model=ProtectionScoreResponse)
async def enable_protection(
    model_id: int,
    payload: ProtectionConfig,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Model).where(Model.id == model_id))
    model_row = result.scalar_one_or_none()

    if not model_row:
        raise HTTPException(status_code=404, detail="Model not found")

    if model_row.base_trust_score is None:
        raise HTTPException(
            status_code=400,
            detail="Model has no base trust score. Run assessment scan first.",
        )

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
    model_row.scan_status = "protected"

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


@router.post("/{model_id}/disable", response_model=ProtectionScoreResponse)
async def disable_protection(
    model_id: int,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Model).where(Model.id == model_id))
    model_row = result.scalar_one_or_none()

    if not model_row:
        raise HTTPException(status_code=404, detail="Model not found")

    if model_row.base_trust_score is None:
        raise HTTPException(
            status_code=400,
            detail="Model has no base trust score stored.",
        )

    model_row.secure_mode_enabled = False
    model_row.protected_score = model_row.base_trust_score
    model_row.scan_status = "completed"

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


@router.get("/{model_id}/score", response_model=ProtectionScoreResponse)
async def get_protection_score(
    model_id: int,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Model).where(Model.id == model_id))
    model_row = result.scalar_one_or_none()

    if not model_row:
        raise HTTPException(status_code=404, detail="Model not found")

    if model_row.base_trust_score is None:
        raise HTTPException(
            status_code=400,
            detail="Model has no base trust score stored.",
        )

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