from fastapi import HTTPException, status

from app.schemas import ScanStatus

READY_SCAN_STATUSES = {
    ScanStatus.COMPLETED.value,
    ScanStatus.PROTECTED.value,
}


def normalize_scan_status(scan_status: str | None) -> str:
    return (scan_status or ScanStatus.PENDING.value).lower()


def build_model_not_ready_error(model_id: int, scan_status: str | None, action: str) -> dict:
    normalized = normalize_scan_status(scan_status)
    return {
        "code": "MODEL_NOT_READY",
        "message": (
            f"Model {model_id} is not ready for {action}. "
            "Run assessment scan first."
        ),
        "context": {
            "model_id": model_id,
            "action": action,
            "scan_status": normalized,
            "required_scan_statuses": sorted(READY_SCAN_STATUSES),
        },
    }


def ensure_model_ready(model_row, action: str) -> None:
    normalized = normalize_scan_status(model_row.scan_status)
    if model_row.base_trust_score is not None and normalized in READY_SCAN_STATUSES:
        return

    raise HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail=build_model_not_ready_error(model_row.id, model_row.scan_status, action),
    )
