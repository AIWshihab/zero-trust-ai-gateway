from fastapi import APIRouter, HTTPException, status, Depends

from app.core.security import require_active_user, require_admin
from app.models.schemas import ModelCreate, ModelOut, TokenData
from app.models.registry import (
    register_model,
    get_model,
    get_all_models,
    deactivate_model,
)

router = APIRouter()


# ─── Get All Models ───────────────────────────────────────────────────────────

@router.get("/", response_model=list[ModelOut])
async def list_models(
    current_user: TokenData = Depends(require_active_user),
):
    """
    Returns all registered AI models.
    Available to any authenticated user.
    """
    return get_all_models()


# ─── Get Single Model ─────────────────────────────────────────────────────────

@router.get("/{model_id}", response_model=ModelOut)
async def get_single_model(
    model_id: int,
    current_user: TokenData = Depends(require_active_user),
):
    """
    Returns metadata for a specific model by ID.
    """
    model = get_model(model_id)
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Model with id {model_id} not found",
        )
    return model


# ─── Register New Model ───────────────────────────────────────────────────────

@router.post("/", response_model=ModelOut, status_code=status.HTTP_201_CREATED)
async def create_model(
    model: ModelCreate,
    current_user: TokenData = Depends(require_admin),
):
    """
    Registers a new AI model into the registry.
    Admin only.
    """
    return register_model(model)


# ─── Deactivate Model ─────────────────────────────────────────────────────────

@router.delete("/{model_id}", status_code=status.HTTP_200_OK)
async def remove_model(
    model_id: int,
    current_user: TokenData = Depends(require_admin),
):
    """
    Deactivates a model (soft delete).
    Admin only.
    """
    success = deactivate_model(model_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Model with id {model_id} not found",
        )
    return {"message": f"Model {model_id} deactivated successfully"}


# ─── Get Model Risk Info ──────────────────────────────────────────────────────

@router.get("/{model_id}/risk", status_code=status.HTTP_200_OK)
async def get_model_risk_info(
    model_id: int,
    current_user: TokenData = Depends(require_active_user),
):
    """
    Returns computed risk and sensitivity scores for a model.
    Used by the policy engine and monitoring dashboard.
    """
    from app.models.registry import get_model_risk_score, get_model_sensitivity_score

    model = get_model(model_id)
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Model with id {model_id} not found",
        )

    return {
        "model_id": model_id,
        "name": model.name,
        "risk_level": model.risk_level,
        "sensitivity_level": model.sensitivity_level,
        "risk_score": get_model_risk_score(model_id),
        "sensitivity_score": get_model_sensitivity_score(model_id),
    }
