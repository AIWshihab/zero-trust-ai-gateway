from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import require_active_user
from app.schemas import TokenData
from app.services.research_evaluation import (
    build_control_effectiveness,
    build_counterfactual_analysis,
    build_evaluation_dataset,
    build_policy_replay,
    build_research_evaluation_report,
    build_risk_drift,
)

router = APIRouter()


def _scope_user_id(current_user: TokenData) -> int | None:
    return None if "admin" in (current_user.scopes or []) else current_user.user_id


@router.get("/evaluation-report")
async def evaluation_report(
    limit: int = Query(default=5000, ge=1, le=10000),
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(require_active_user),
):
    return await build_research_evaluation_report(db, limit=limit, user_id=_scope_user_id(current_user))


@router.get("/evaluation-dataset")
async def evaluation_dataset(
    limit: int = Query(default=5000, ge=1, le=10000),
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(require_active_user),
):
    if "admin" not in (current_user.scopes or []):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Research-safe dataset export is admin-only. Users can run scoped evaluation and replay on their own data.",
        )
    return await build_evaluation_dataset(db, limit=limit)


@router.get("/policy-replay")
async def policy_replay(
    limit: int = Query(default=5000, ge=1, le=10000),
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(require_active_user),
):
    return await build_policy_replay(db, limit=limit, user_id=_scope_user_id(current_user))


@router.get("/control-effectiveness")
async def control_effectiveness(
    limit: int = Query(default=5000, ge=1, le=10000),
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(require_active_user),
):
    return await build_control_effectiveness(db, limit=limit, user_id=_scope_user_id(current_user))


@router.get("/counterfactual-analysis")
async def counterfactual_analysis(
    limit: int = Query(default=250, ge=1, le=2000),
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(require_active_user),
):
    return await build_counterfactual_analysis(db, limit=limit, user_id=_scope_user_id(current_user))


@router.get("/risk-drift")
async def risk_drift(
    bucket: str = Query(default="hourly", pattern="^(hourly|daily)$"),
    limit: int = Query(default=5000, ge=1, le=10000),
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(require_active_user),
):
    return await build_risk_drift(db, bucket=bucket, limit=limit, user_id=_scope_user_id(current_user))
