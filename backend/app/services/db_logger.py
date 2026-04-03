from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.request_log import RequestLog
from app.schemas import RequestDecision


def _normalize_decision(value) -> str:
    if hasattr(value, "value"):
        return value.value
    return str(value)


async def log_request_db(
    db: AsyncSession,
    *,
    user_id: Optional[int],
    model_id: int,
    prompt_hash: str,
    security_score: float,
    decision: RequestDecision,
    latency_ms: float,
    prompt_risk_score: Optional[float] = None,
    output_risk_score: Optional[float] = None,
    blocked: Optional[bool] = None,
    secure_mode_enabled: Optional[bool] = None,
    reason: Optional[str] = None,
) -> RequestLog:
    row = RequestLog(
        user_id=user_id,
        model_id=model_id,
        prompt_hash=prompt_hash,
        security_score=float(security_score),
        prompt_risk_score=float(prompt_risk_score) if prompt_risk_score is not None else None,
        output_risk_score=float(output_risk_score) if output_risk_score is not None else None,
        decision=_normalize_decision(decision),
        blocked=bool(blocked) if blocked is not None else False,
        secure_mode_enabled=bool(secure_mode_enabled) if secure_mode_enabled is not None else False,
        reason=reason,
        latency_ms=float(latency_ms),
    )

    db.add(row)
    await db.flush()
    await db.commit()
    await db.refresh(row)
    return row
