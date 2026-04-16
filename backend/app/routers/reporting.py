import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func, case
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import require_active_user
from app.models.model import Model
from app.models.request_log import RequestLog
from app.schemas import ComparisonReportResponse, ErrorResponse, TokenData
from app.services.model_readiness import ensure_model_ready

router = APIRouter()


def _safe_float(value, default=0.0):
    try:
        return float(value)
    except Exception:
        return default


@router.get(
    "/{model_id}/comparison",
    response_model=ComparisonReportResponse,
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        409: {"model": ErrorResponse, "description": "Model not ready"},
        404: {"model": ErrorResponse, "description": "Model not found"},
    },
)
async def get_model_comparison_report(
    model_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(require_active_user),
):
    model_result = await db.execute(select(Model).where(Model.id == model_id))
    model_row = model_result.scalar_one_or_none()

    if not model_row:
        raise HTTPException(status_code=404, detail="Model not found")
    ensure_model_ready(model_row, action="reporting")

    metrics_query = select(
        func.count(RequestLog.id).label("total_requests"),
        func.sum(case((RequestLog.decision == "block", 1), else_=0)).label("blocked_requests"),
        func.sum(case((RequestLog.decision == "challenge", 1), else_=0)).label("challenged_requests"),
        func.sum(case((RequestLog.decision == "allow", 1), else_=0)).label("allowed_requests"),
        func.avg(RequestLog.prompt_risk_score).label("avg_prompt_risk_score"),
        func.avg(RequestLog.output_risk_score).label("avg_output_risk_score"),
        func.avg(RequestLog.latency_ms).label("avg_latency_ms"),
    ).where(RequestLog.model_id == model_id)

    metrics_result = await db.execute(metrics_query)
    row = metrics_result.one()

    total_requests = int(row.total_requests or 0)
    blocked_requests = int(row.blocked_requests or 0)
    challenged_requests = int(row.challenged_requests or 0)
    allowed_requests = int(row.allowed_requests or 0)

    avg_prompt_risk_score = _safe_float(row.avg_prompt_risk_score, 0.0)
    avg_output_risk_score = _safe_float(row.avg_output_risk_score, 0.0)
    avg_latency_ms = _safe_float(row.avg_latency_ms, 0.0)

    base_trust_score = _safe_float(model_row.base_trust_score, 0.0)
    protected_score = _safe_float(
        model_row.protected_score if model_row.protected_score is not None else model_row.base_trust_score,
        0.0,
    )
    improvement_delta = max(0.0, protected_score - base_trust_score)

    latest_findings = []
    recommendations = []

    if model_row.scan_summary_json:
        try:
            scan_summary = json.loads(model_row.scan_summary_json)
            latest_findings = scan_summary.get("findings", [])[:8]
        except Exception:
            latest_findings = []

    if base_trust_score < 70:
        recommendations.append("Improve pre-use trust posture by strengthening model onboarding checks.")
    if not bool(model_row.secure_mode_enabled):
        recommendations.append("Enable secure mode to enforce gateway protections.")
    if blocked_requests == 0 and total_requests > 0:
        recommendations.append("Run adversarial test prompts to validate blocking behavior.")
    if avg_prompt_risk_score > 0.35:
        recommendations.append("Tighten prompt guard thresholds for high-risk prompt patterns.")
    if avg_output_risk_score > 10:
        recommendations.append("Strengthen output filtering and response redaction rules.")
    if total_requests == 0:
        recommendations.append("Run live inference requests to generate runtime evidence for this model.")
    if not recommendations:
        recommendations.append("Current protection posture looks stable under observed requests.")

    return ComparisonReportResponse(
        model_id=model_row.id,
        model_name=model_row.name,
        provider_name=model_row.provider_name,
        base_trust_score=round(base_trust_score, 2),
        protected_score=round(protected_score, 2),
        improvement_delta=round(improvement_delta, 2),
        secure_mode_enabled=bool(model_row.secure_mode_enabled),
        total_requests=total_requests,
        blocked_requests=blocked_requests,
        challenged_requests=challenged_requests,
        allowed_requests=allowed_requests,
        blocked_count=blocked_requests,
        challenged_count=challenged_requests,
        allowed_count=allowed_requests,
        avg_prompt_risk_score=round(avg_prompt_risk_score, 4),
        avg_output_risk_score=round(avg_output_risk_score, 2),
        avg_latency_ms=round(avg_latency_ms, 2),
        latest_findings=latest_findings,
        recommendations=recommendations,
    )
