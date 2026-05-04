from fastapi import APIRouter, Depends

from app.core.security import require_admin
from app.schemas import TokenData
from app.testing.runner import run_soc_tests

router = APIRouter()


@router.get("/run-soc-tests")
async def run_soc_tests_endpoint(
    current_user: TokenData = Depends(require_admin),
):
    return run_soc_tests()
