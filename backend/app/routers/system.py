from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import require_active_user
from app.core.system_state import get_system_state
from app.schemas import TokenData

router = APIRouter()


@router.get("/state")
async def system_state_endpoint(
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(require_active_user),
):
    """
    Unified system state endpoint.
    Always returns valid data — falls back through DB → static mock.
    """
    return await get_system_state(db)
