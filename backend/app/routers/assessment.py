import json
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.model import Model
from app.models.schemas import ModelCreate
from app.services.model_scanner import scan_model

router = APIRouter()


def _normalize_model_type(value: str | None) -> str:
    if not value:
        return "custom_api"
    return value.lower()


def _default_sensitivity() -> str:
    return "medium"


def _default_risk() -> str:
    return "medium"


@router.post("/scan")
async def scan_and_register_model(
    payload: ModelCreate,
    db: AsyncSession = Depends(get_db),
):
    try:
        scan_result = await scan_model(
            name=payload.name,
            model_type=payload.model_type.value if hasattr(payload.model_type, "value") else str(payload.model_type),
            provider_name=getattr(payload, "provider_name", None),
            source_url=getattr(payload, "source_url", None),
            hf_model_id=getattr(payload, "hf_model_id", None),
            endpoint=payload.endpoint,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Scan failed: {exc}")

    existing_query = select(Model).where(
        Model.name == payload.name,
        Model.provider_name == getattr(payload, "provider_name", None),
        Model.endpoint == payload.endpoint,
    )
    existing_result = await db.execute(existing_query)
    model_row = existing_result.scalar_one_or_none()

    if model_row is None:
        model_row = Model(
            name=payload.name,
            description=payload.description,
            model_type=_normalize_model_type(payload.model_type.value if hasattr(payload.model_type, "value") else payload.model_type),
            sensitivity_level=_default_sensitivity(),
            risk_level=_default_risk(),
            endpoint=payload.endpoint,
            is_active=True,
            source_url=getattr(payload, "source_url", None),
            provider_name=getattr(payload, "provider_name", None),
            hf_model_id=getattr(payload, "hf_model_id", None),
            auth_type=None,
            has_model_card=scan_result["raw_inputs"]["provider_data"].get("has_model_card", False),
            supports_https=scan_result["raw_inputs"]["infrastructure_data"].get("supports_https", False),
            requires_auth=scan_result["raw_inputs"]["infrastructure_data"].get("requires_auth", False),
            base_trust_score=scan_result["base_trust_score"],
            protected_score=None,
            secure_mode_enabled=False,
            scan_status="completed",
            scan_summary_json=json.dumps(scan_result),
            last_scan_at=datetime.now(timezone.utc),
        )
        db.add(model_row)
    else:
        model_row.description = payload.description
        model_row.model_type = _normalize_model_type(payload.model_type.value if hasattr(payload.model_type, "value") else payload.model_type)
        model_row.endpoint = payload.endpoint
        model_row.source_url = getattr(payload, "source_url", None)
        model_row.provider_name = getattr(payload, "provider_name", None)
        model_row.hf_model_id = getattr(payload, "hf_model_id", None)

        model_row.has_model_card = scan_result["raw_inputs"]["provider_data"].get("has_model_card", False)
        model_row.supports_https = scan_result["raw_inputs"]["infrastructure_data"].get("supports_https", False)
        model_row.requires_auth = scan_result["raw_inputs"]["infrastructure_data"].get("requires_auth", False)

        model_row.base_trust_score = scan_result["base_trust_score"]
        model_row.scan_status = "completed"
        model_row.scan_summary_json = json.dumps(scan_result)
        model_row.last_scan_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(model_row)

    return {
        "model_id": model_row.id,
        "base_trust_score": scan_result["base_trust_score"],
        "breakdown": scan_result["breakdown"],
        "findings": scan_result["findings"],
        "limitations": scan_result["limitations"],
    }