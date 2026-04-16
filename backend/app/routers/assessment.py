import json
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import require_admin
from app.models.model import Model
from app.models.model_posture_event import ModelPostureEvent
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


def _safe_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except Exception:
        return None


def _safe_int(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except Exception:
        return None


def _parse_iso_datetime(value: Any) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        try:
            normalized = value.replace("Z", "+00:00")
            parsed = datetime.fromisoformat(normalized)
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=timezone.utc)
            return parsed
        except Exception:
            return None
    return None


def _extract_protection_config(scan_summary_json: str | None) -> dict[str, Any]:
    if not scan_summary_json:
        return {}
    try:
        parsed = json.loads(scan_summary_json)
    except Exception:
        return {}

    protection = parsed.get("protection") if isinstance(parsed, dict) else None
    if not isinstance(protection, dict):
        return {}
    config = protection.get("config")
    if not isinstance(config, dict):
        return {}
    return config


def _to_scan_response(model_row: Model, scan_result: dict) -> ModelScanResponse:
    persisted_factors = model_row.posture_factors or {}
    persisted_controls = persisted_factors.get("secured_risk_controls") if isinstance(persisted_factors, dict) else None

    risk_reduction_explanations = scan_result.get("risk_reduction_explanations") or []
    if not risk_reduction_explanations and isinstance(persisted_controls, dict):
        controls = persisted_controls.get("controls") or []
        risk_reduction_explanations = [
            (
                f"{c.get('control_name')} lowered risk by {c.get('applied_reduction_points', 0)} points "
                f"({round(float(c.get('applied_reduction_ratio', 0)) * 100, 2)}% of base risk)."
            )
            for c in controls
            if isinstance(c, dict) and c.get("active")
        ]

    return ModelScanResponse(
        model_id=model_row.id,
        model_name=model_row.name,
        name=model_row.name,
        model_type=model_row.model_type,
        provider_name=model_row.provider_name,
        base_trust_score=scan_result["base_trust_score"],
        breakdown=scan_result["breakdown"],
        base_risk_score=model_row.base_risk_score,
        secured_risk_score=model_row.secured_risk_score,
        risk_reduction_pct=model_row.risk_reduction_pct,
        posture_factors=persisted_factors,
        secured_risk_controls=persisted_controls or {},
        posture_explanations=model_row.posture_explanations or [],
        risk_reduction_explanations=risk_reduction_explanations,
        posture_assessed_at=model_row.posture_assessed_at,
        posture_expires_at=model_row.posture_expires_at,
        scan_valid_until=model_row.scan_valid_until,
        findings=scan_result["findings"],
        limitations=scan_result["limitations"],
        secure_mode_enabled=bool(model_row.secure_mode_enabled),
        scan_status=model_row.scan_status or ScanStatus.COMPLETED.value,
        scanned_at=model_row.last_scan_at or model_row.posture_assessed_at,
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

    # Keep previous protection context so secured-risk scoring can reflect active controls.
    previous_scan_at = model_row.last_scan_at
    protection_config = _extract_protection_config(model_row.scan_summary_json)

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
            description=payload.description,
            secure_mode_enabled=bool(model_row.secure_mode_enabled),
            protection_config=protection_config,
            previous_scan_at=previous_scan_at,
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

    previous_base_risk = _safe_float(model_row.base_risk_score)
    previous_secured_risk = _safe_float(model_row.secured_risk_score)
    previous_reduction = _safe_float(model_row.risk_reduction_pct)

    base_risk_score = _safe_float(scan_result.get("base_risk_score"))
    secured_risk_score = _safe_float(scan_result.get("secured_risk_score"))
    risk_reduction_pct = _safe_float(scan_result.get("risk_reduction_pct"))

    model_row.base_risk_score = base_risk_score
    model_row.secured_risk_score = secured_risk_score if secured_risk_score is not None else base_risk_score
    model_row.risk_reduction_pct = risk_reduction_pct if risk_reduction_pct is not None else 0.0

    posture_factors = scan_result.get("posture_factors") or {}
    posture_factors["secured_risk_controls"] = scan_result.get("secured_risk_controls") or {}
    model_row.posture_factors = posture_factors

    model_row.posture_explanations = scan_result.get("posture_explanations") or []

    posture_assessed_at = _parse_iso_datetime(scan_result.get("posture_assessed_at"))
    posture_expires_at = _parse_iso_datetime(scan_result.get("posture_expires_at"))
    scan_valid_until = _parse_iso_datetime(scan_result.get("scan_valid_until"))

    if posture_assessed_at is not None:
        model_row.posture_assessed_at = posture_assessed_at
        model_row.last_reassessed_at = posture_assessed_at
    if posture_expires_at is not None:
        model_row.posture_expires_at = posture_expires_at
    if scan_valid_until is not None:
        model_row.scan_valid_until = scan_valid_until

    model_row.scan_freshness_days = _safe_int(scan_result.get("scan_freshness_days"))

    model_row.scan_status = ScanStatus.PROTECTED.value if model_row.secure_mode_enabled else ScanStatus.COMPLETED.value
    model_row.scan_summary_json = json.dumps(scan_result, default=str)
    model_row.last_scan_at = datetime.now(timezone.utc)

    scan_event_context = {
        "scan_status": model_row.scan_status,
        "secure_mode_enabled": bool(model_row.secure_mode_enabled),
        "scan_valid_until": model_row.scan_valid_until.isoformat() if model_row.scan_valid_until else None,
        "scan_freshness_days": model_row.scan_freshness_days,
    }
    base_after = _safe_float(model_row.base_risk_score)
    secured_after = _safe_float(model_row.secured_risk_score)
    reduction_after = _safe_float(model_row.risk_reduction_pct)

    if previous_base_risk is None or base_after is None or abs(previous_base_risk - base_after) >= 0.01:
        db.add(
            ModelPostureEvent(
                model_id=model_row.id,
                model_name_snapshot=model_row.name,
                event_type="model_scan_reassessment",
                metric_name="base_risk_score",
                previous_value=previous_base_risk,
                new_value=base_after,
                reason="Model scan/rescan updated base risk posture.",
                context_json=scan_event_context,
            )
        )

    if previous_secured_risk is None or secured_after is None or abs(previous_secured_risk - secured_after) >= 0.01:
        db.add(
            ModelPostureEvent(
                model_id=model_row.id,
                model_name_snapshot=model_row.name,
                event_type="model_scan_reassessment",
                metric_name="secured_risk_score",
                previous_value=previous_secured_risk,
                new_value=secured_after,
                reason="Model scan/rescan updated secured risk posture.",
                context_json=scan_event_context,
            )
        )

    if previous_reduction is None or reduction_after is None or abs(previous_reduction - reduction_after) >= 0.01:
        db.add(
            ModelPostureEvent(
                model_id=model_row.id,
                model_name_snapshot=model_row.name,
                event_type="model_scan_reassessment",
                metric_name="risk_reduction_pct",
                previous_value=previous_reduction,
                new_value=reduction_after,
                reason="Model scan/rescan updated risk reduction posture.",
                context_json=scan_event_context,
            )
        )

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
