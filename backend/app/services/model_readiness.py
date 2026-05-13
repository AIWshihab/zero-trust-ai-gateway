from fastapi import HTTPException, status

from app.schemas import ScanStatus
from app.services.chat_errors import model_setup_error

READY_SCAN_STATUSES = {
    ScanStatus.COMPLETED.value,
    ScanStatus.PROTECTED.value,
}


def normalize_scan_status(scan_status: str | None) -> str:
    return (scan_status or ScanStatus.PENDING.value).lower()


def build_model_not_ready_error(model_id: int, scan_status: str | None, action: str) -> dict:
    normalized = normalize_scan_status(scan_status)
    return model_setup_error(
        code="model_needs_assessment",
        title="Needs assessment",
        reason=f"Model {model_id} has scan status '{normalized}'.",
        explanation="The gateway can pre-screen the prompt, but it will not send traffic to a model until the model has a completed or protected assessment.",
        suggested_fix="Ask an admin to run the model security assessment and enable protection before using this model for chat.",
        action_required="admin",
        metadata={
            "model_id": model_id,
            "action": action,
            "scan_status": normalized,
            "required_scan_statuses": sorted(READY_SCAN_STATUSES),
        },
    )


def ensure_model_ready(model_row, action: str) -> None:
    normalized = normalize_scan_status(model_row.scan_status)
    if model_row.base_trust_score is not None and normalized in READY_SCAN_STATUSES:
        return

    raise HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail=build_model_not_ready_error(model_row.id, model_row.scan_status, action),
    )
