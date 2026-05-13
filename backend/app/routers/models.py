from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, HTTPException, Query, status, Depends

from app.core.security import require_active_user, require_admin
from app.core.database import get_db
from app.schemas import (
    ErrorResponse,
    MessageResponse,
    ModelCreate,
    ModelOut,
    ModelRiskInfoResponse,
    TokenData,
    ScanStatus,
    RiskLevel,
    SensitivityLevel,
)
from app.schemas.device import UserModelCreate
from app.services.model_registry import (
    register_model,
    get_model,
    get_all_models,
    deactivate_model,
    get_model_risk_score,
    get_model_sensitivity_score,
)
from app.services.model_runtime import get_model_runtime_status
from app.services.device_service import count_user_models, USER_MODEL_LIMIT
from app.models.model import Model

router = APIRouter()

USER_MODEL_LIMIT = 3


# ── Helper ────────────────────────────────────────────────────────────────────

async def _get_visible_models(
    db: AsyncSession,
    user_id: int,
    is_admin: bool,
    include_inactive: bool = False,
) -> list[ModelOut]:
    """Return models visible to this user: global + their own private."""
    q = select(Model)
    if not include_inactive:
        q = q.where(Model.is_active.is_(True))
    if not is_admin:
        from sqlalchemy import or_
        q = q.where(
            or_(
                Model.visibility == "global",
                Model.owner_user_id == user_id,
            )
        )
    result = await db.execute(q.order_by(Model.created_at.desc(), Model.id.desc()))
    return [ModelOut.model_validate(m) for m in result.scalars().all()]


# ── Standard listing endpoints ────────────────────────────────────────────────

@router.get(
    "/",
    response_model=list[ModelOut],
    responses={401: {"model": ErrorResponse}},
)
async def list_models(
    include_inactive: bool = Query(default=False),
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(require_active_user),
):
    is_admin = "admin" in (current_user.scopes or [])
    if include_inactive and not is_admin:
        include_inactive = False
    return await _get_visible_models(db, current_user.user_id or 0, is_admin, include_inactive)


@router.get(
    "/runtime-readiness",
    responses={401: {"model": ErrorResponse}},
)
async def list_model_runtime_readiness(
    include_inactive: bool = Query(default=False),
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(require_active_user),
):
    is_admin = "admin" in (current_user.scopes or [])
    if include_inactive and not is_admin:
        include_inactive = False
    models = await _get_visible_models(db, current_user.user_id or 0, is_admin, include_inactive)
    return [get_model_runtime_status(m) for m in models]


# ── User-owned model endpoints ────────────────────────────────────────────────

@router.get(
    "/my",
    response_model=list[ModelOut],
    responses={401: {"model": ErrorResponse}},
)
async def list_my_models(
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(require_active_user),
):
    """Return only models owned by the current user."""
    if not current_user.user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    result = await db.execute(
        select(Model)
        .where(Model.owner_user_id == current_user.user_id)
        .order_by(Model.created_at.desc())
    )
    return [ModelOut.model_validate(m) for m in result.scalars().all()]


@router.post(
    "/my",
    response_model=ModelOut,
    status_code=status.HTTP_201_CREATED,
    responses={
        401: {"model": ErrorResponse},
        403: {"model": ErrorResponse, "description": "Model limit reached"},
        422: {"model": ErrorResponse},
    },
)
async def create_my_model(
    body: UserModelCreate,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(require_active_user),
):
    """Create a user-owned model. Max 3 per user, enforced server-side."""
    if not current_user.user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    count = await count_user_models(db, current_user.user_id)
    if count >= USER_MODEL_LIMIT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "model_limit_reached",
                "message": f"You have reached the maximum of {USER_MODEL_LIMIT} models. Delete an existing model to add a new one.",
                "current_count": count,
                "limit": USER_MODEL_LIMIT,
            },
        )

    # Map string type to enum value safely
    from app.schemas.enums import ModelType
    try:
        model_type = ModelType(body.model_type)
    except ValueError:
        raise HTTPException(status_code=422, detail=f"Invalid model_type: {body.model_type}")

    db_model = Model(
        name=body.name,
        description=body.description,
        model_type=model_type,
        sensitivity_level=SensitivityLevel.MEDIUM,
        risk_level=RiskLevel.MEDIUM,
        endpoint=body.endpoint,
        provider_name=body.provider_name,
        hf_model_id=body.hf_model_id,
        auth_type=body.auth_type,
        is_active=True,
        scan_status=ScanStatus.PENDING.value,
        secure_mode_enabled=False,
        owner_user_id=current_user.user_id,
        visibility=body.visibility,
    )
    db.add(db_model)
    await db.commit()
    await db.refresh(db_model)
    return ModelOut.model_validate(db_model)


@router.delete(
    "/my/{model_id}",
    response_model=MessageResponse,
    responses={
        401: {"model": ErrorResponse},
        403: {"model": ErrorResponse, "description": "Not your model"},
        404: {"model": ErrorResponse},
    },
)
async def delete_my_model(
    model_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(require_active_user),
):
    """Deactivate a user-owned model. Users can only delete their own models."""
    if not current_user.user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    result = await db.execute(select(Model).where(Model.id == model_id))
    model = result.scalar_one_or_none()
    if not model:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Model not found")
    if model.owner_user_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete your own models",
        )
    model.is_active = False
    await db.commit()
    return {"message": f"Model {model_id} removed."}


# ── Single model + admin endpoints ────────────────────────────────────────────

@router.get(
    "/{model_id}",
    response_model=ModelOut,
    responses={
        401: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
    },
)
async def get_single_model(
    model_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(require_active_user),
):
    model = await get_model(db=db, model_id=model_id)
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Model with id {model_id} not found",
        )
    return model


@router.post(
    "/",
    response_model=ModelOut,
    status_code=status.HTTP_201_CREATED,
    responses={
        401: {"model": ErrorResponse},
        403: {"model": ErrorResponse, "description": "Admin access required"},
    },
)
async def create_model(
    model: ModelCreate,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(require_admin),
):
    return await register_model(db=db, model=model)


@router.delete(
    "/{model_id}",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    responses={
        401: {"model": ErrorResponse},
        403: {"model": ErrorResponse, "description": "Admin access required"},
        404: {"model": ErrorResponse},
    },
)
async def remove_model(
    model_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(require_admin),
):
    success = await deactivate_model(db=db, model_id=model_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Model with id {model_id} not found",
        )
    return {"message": f"Model {model_id} deactivated successfully"}


@router.get(
    "/{model_id}/risk",
    response_model=ModelRiskInfoResponse,
    responses={
        401: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
    },
)
async def get_model_risk_info(
    model_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(require_active_user),
):
    model = await get_model(db=db, model_id=model_id)
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Model with id {model_id} not found",
        )

    risk_score = await get_model_risk_score(db=db, model_id=model_id)
    sensitivity_score = await get_model_sensitivity_score(db=db, model_id=model_id)

    return {
        "model_id": model_id,
        "name": model.name,
        "risk_level": model.risk_level,
        "sensitivity_level": model.sensitivity_level,
        "risk_score": risk_score,
        "sensitivity_score": sensitivity_score,
        "secure_mode_enabled": bool(getattr(model, "secure_mode_enabled", False)),
    }
