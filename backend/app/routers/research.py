from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import require_admin
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


@router.get("/evaluation-report")
async def evaluation_report(
    limit: int = Query(default=5000, ge=1, le=10000),
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(require_admin),
):
    return await build_research_evaluation_report(db, limit=limit)


@router.get("/evaluation-dataset")
async def evaluation_dataset(
    limit: int = Query(default=5000, ge=1, le=10000),
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(require_admin),
):
    return await build_evaluation_dataset(db, limit=limit)


@router.get("/policy-replay")
async def policy_replay(
    limit: int = Query(default=5000, ge=1, le=10000),
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(require_admin),
):
    return await build_policy_replay(db, limit=limit)


@router.get("/control-effectiveness")
async def control_effectiveness(
    limit: int = Query(default=5000, ge=1, le=10000),
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(require_admin),
):
    return await build_control_effectiveness(db, limit=limit)


@router.get("/counterfactual-analysis")
async def counterfactual_analysis(
    limit: int = Query(default=250, ge=1, le=2000),
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(require_admin),
):
    return await build_counterfactual_analysis(db, limit=limit)


@router.get("/risk-drift")
async def risk_drift(
    bucket: str = Query(default="hourly", pattern="^(hourly|daily)$"),
    limit: int = Query(default=5000, ge=1, le=10000),
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(require_admin),
):
    return await build_risk_drift(db, bucket=bucket, limit=limit)
