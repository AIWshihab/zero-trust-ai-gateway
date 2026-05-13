import asyncio
import logging

from fastapi import APIRouter, Depends

from app.core.security import require_active_user
from app.schemas import TokenData
from app.testing.runner import run_soc_tests

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/run-soc-tests")
async def run_soc_tests_endpoint(
    current_user: TokenData = Depends(require_active_user),
):
    # Run in a thread so pytest can create its own event loop without
    # conflicting with the running FastAPI/uvicorn asyncio loop.
    try:
        result = await asyncio.to_thread(run_soc_tests)
        return result
    except Exception as exc:
        logger.exception("Test runner failed: %s", exc)
        return {
            "total": 0,
            "passed": 0,
            "failed": 0,
            "duration": 0.0,
            "tests": [],
            "failures": [{"test": "runner_error", "error": str(exc)}],
        }
