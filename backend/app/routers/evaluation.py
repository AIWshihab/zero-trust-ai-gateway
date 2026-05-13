from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import require_active_user
from app.evaluation.engine import compare_scenario
from app.evaluation.scenarios import SCENARIOS, get_scenario, list_scenarios
from app.schemas import TokenData

router = APIRouter()


@router.get("/scenarios")
async def evaluation_scenarios(
    current_user: TokenData = Depends(require_active_user),
):
    return {"scenarios": list_scenarios()}


@router.get("/compare/{scenario_id}")
async def evaluation_compare(
    scenario_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(require_active_user),
):
    scenario = get_scenario(scenario_id)
    if scenario is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evaluation scenario not found")
    return await compare_scenario(db, scenario, user_id=getattr(current_user, "user_id", None))


@router.get("/report")
async def evaluation_report(
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(require_active_user),
):
    user_id = getattr(current_user, "user_id", None)
    return {
        "scenarios": [
            await compare_scenario(db, scenario, user_id=user_id)
            for scenario in SCENARIOS
        ]
    }
