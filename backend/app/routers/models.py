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
)
from app.services.model_registry import (
    register_model,
    get_model,
    get_all_models,
    deactivate_model,
    get_model_risk_score,
    get_model_sensitivity_score,
)
from app.services.model_runtime import get_model_runtime_status

router = APIRouter()


@router.get(
    "/",
    response_model=list[ModelOut],
    responses={401: {"model": ErrorResponse, "description": "Unauthorized"}},
)
async def list_models(
    include_inactive: bool = Query(default=False),
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(require_active_user),
):
    if include_inactive and "admin" not in (current_user.scopes or []):
        include_inactive = False
    return await get_all_models(db=db, include_inactive=include_inactive)


@router.get(
    "/runtime-readiness",
    responses={401: {"model": ErrorResponse, "description": "Unauthorized"}},
)
async def list_model_runtime_readiness(
    include_inactive: bool = Query(default=False),
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(require_active_user),
):
    if include_inactive and "admin" not in (current_user.scopes or []):
        include_inactive = False
    models = await get_all_models(db=db, include_inactive=include_inactive)
    return [get_model_runtime_status(model) for model in models]


@router.get(
    "/{model_id}",
    response_model=ModelOut,
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        404: {"model": ErrorResponse, "description": "Model not found"},
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
        401: {"model": ErrorResponse, "description": "Unauthorized"},
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
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Admin access required"},
        404: {"model": ErrorResponse, "description": "Model not found"},
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
    status_code=status.HTTP_200_OK,
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        404: {"model": ErrorResponse, "description": "Model not found"},
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
