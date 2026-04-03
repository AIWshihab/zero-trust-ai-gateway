import json
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import require_admin
from app.models.model import Model
from app.schemas import (
    ErrorResponse,
    ModelScanRequest,
    ModelScanResponse,
    ModelType,
    RiskLevel,
    ScanStatus,
    SensitivityLevel,
    TokenData,
)
from app.services.model_scanner import scan_model

router = APIRouter()


def _scan_failed_detail(model_id: int, exc: Exception) -> dict:
    return {
        "code": "SCAN_FAILED",
        "message": "Model assessment scan failed.",
        "context": {
            "model_id": model_id,
            "error": str(exc),
        },
    }


def _build_scan_payload_from_model(model_row: Model) -> ModelScanRequest:
    model_type = model_row.model_type
    if model_type is None:
        model_type = ModelType.CUSTOM_API

    return ModelScanRequest(
        name=model_row.name,
        model_type=model_type,
        provider_name=model_row.provider_name,
        source_url=model_row.source_url,
        hf_model_id=model_row.hf_model_id,
        endpoint=model_row.endpoint,
        description=model_row.description,
    )


def _to_scan_response(model_row: Model, scan_result: dict) -> ModelScanResponse:
    return ModelScanResponse(
        model_id=model_row.id,
        model_name=model_row.name,
        model_type=model_row.model_type,
        provider_name=model_row.provider_name,
        base_trust_score=scan_result["base_trust_score"],
        breakdown=scan_result["breakdown"],
        findings=scan_result["findings"],
        limitations=scan_result["limitations"],
        secure_mode_enabled=bool(model_row.secure_mode_enabled),
        scan_status=model_row.scan_status or ScanStatus.COMPLETED.value,
        raw_inputs=scan_result.get("raw_inputs", {}),
    )


async def _apply_scan(
    db: AsyncSession,
    model_row: Model,
    payload: ModelScanRequest,
) -> ModelScanResponse:
    model_row.name = payload.name
    model_row.description = payload.description
    model_row.model_type = payload.model_type
    model_row.endpoint = payload.endpoint
    model_row.source_url = payload.source_url
    model_row.provider_name = payload.provider_name
    model_row.hf_model_id = payload.hf_model_id

    if model_row.sensitivity_level is None:
        model_row.sensitivity_level = SensitivityLevel.MEDIUM
    if model_row.risk_level is None:
        model_row.risk_level = RiskLevel.MEDIUM

    model_row.is_active = True
    model_row.scan_status = ScanStatus.IN_PROGRESS.value

    await db.commit()
    await db.refresh(model_row)

    try:
        scan_result = await scan_model(
            name=payload.name,
            model_type=payload.model_type.value,
            provider_name=payload.provider_name,
            source_url=payload.source_url,
            hf_model_id=payload.hf_model_id,
            endpoint=payload.endpoint,
        )
    except Exception as exc:
        model_row.scan_status = ScanStatus.FAILED.value
        model_row.scan_summary_json = json.dumps({"error": str(exc)})
        model_row.last_scan_at = datetime.now(timezone.utc)
        await db.commit()
        raise HTTPException(status_code=500, detail=_scan_failed_detail(model_row.id, exc))

    provider_data = scan_result.get("raw_inputs", {}).get("provider_data", {})
    infrastructure_data = scan_result.get("raw_inputs", {}).get("infrastructure_data", {})

    model_row.has_model_card = bool(provider_data.get("has_model_card", False))
    model_row.supports_https = bool(infrastructure_data.get("supports_https", False))
    model_row.requires_auth = bool(infrastructure_data.get("requires_auth", False))

    model_row.base_trust_score = scan_result["base_trust_score"]
    if model_row.secure_mode_enabled and model_row.protected_score is None:
        model_row.protected_score = model_row.base_trust_score

    model_row.scan_status = (
        ScanStatus.PROTECTED.value
        if model_row.secure_mode_enabled
        else ScanStatus.COMPLETED.value
    )
    model_row.scan_summary_json = json.dumps(scan_result)
    model_row.last_scan_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(model_row)

    return _to_scan_response(model_row, scan_result)


@router.post(
    "/scan",
    response_model=ModelScanResponse,
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Admin access required"},
        500: {"model": ErrorResponse, "description": "Scan failed"},
    },
)
async def scan_and_register_model(
    payload: ModelScanRequest,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(require_admin),
):
    existing_query = select(Model).where(
        Model.name == payload.name,
        Model.provider_name == payload.provider_name,
        Model.endpoint == payload.endpoint,
    )
    existing_result = await db.execute(existing_query)
    model_row = existing_result.scalar_one_or_none()

    if model_row is None:
        model_row = Model(
            name=payload.name,
            description=payload.description,
            model_type=payload.model_type,
            sensitivity_level=SensitivityLevel.MEDIUM,
            risk_level=RiskLevel.MEDIUM,
            endpoint=payload.endpoint,
            is_active=True,
            source_url=payload.source_url,
            provider_name=payload.provider_name,
            hf_model_id=payload.hf_model_id,
            auth_type=None,
            has_model_card=False,
            supports_https=False,
            requires_auth=False,
            base_trust_score=None,
            protected_score=None,
            secure_mode_enabled=False,
            scan_status=ScanStatus.PENDING.value,
            scan_summary_json=None,
            last_scan_at=None,
        )
        db.add(model_row)
        await db.commit()
        await db.refresh(model_row)

    return await _apply_scan(db=db, model_row=model_row, payload=payload)


@router.post(
    "/{model_id}/scan",
    response_model=ModelScanResponse,
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Admin access required"},
        404: {"model": ErrorResponse, "description": "Model not found"},
        500: {"model": ErrorResponse, "description": "Scan failed"},
    },
)
async def rescan_registered_model(
    model_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(require_admin),
):
    model_result = await db.execute(select(Model).where(Model.id == model_id))
    model_row = model_result.scalar_one_or_none()
    if not model_row:
        raise HTTPException(status_code=404, detail=f"Model {model_id} not found")

    payload = _build_scan_payload_from_model(model_row)
    return await _apply_scan(db=db, model_row=model_row, payload=payload)
