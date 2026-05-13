"""Device + session management endpoints.

GET  /api/v1/devices/me               — user's own devices
GET  /api/v1/devices/me/sessions      — user's own sessions
GET  /api/v1/devices/me/events        — user's own SOC events
GET  /api/v1/devices/admin            — admin: all devices
GET  /api/v1/devices/admin/events     — admin: all device events
POST /api/v1/devices/{id}/trust       — admin: set trust/revoke
POST /api/v1/devices/{id}/revoke      — admin: revoke device
POST /api/v1/sessions/{id}/revoke     — user/admin: revoke session
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import require_active_user, require_admin
from app.schemas import ErrorResponse, MessageResponse, TokenData
from app.schemas.device import (
    CurrentDeviceInfo,
    DeviceAdminOut,
    DeviceEventOut,
    DeviceOut,
    DeviceTrustUpdate,
    UserSessionOut,
)
from app.services.device_service import (
    _make_fingerprint,
    _get_client_ip,
    _parse_user_agent,
    _hash,
    get_all_device_events,
    get_all_devices,
    get_current_device_info,
    get_device_events_for_user,
    get_devices_for_user,
    get_sessions_for_user,
    revoke_device,
    revoke_session,
    set_device_trust,
)

router = APIRouter()


# ── User endpoints ────────────────────────────────────────────────────────────

def _extract_token(request: Request) -> str:
    auth = request.headers.get("Authorization", "")
    if auth.lower().startswith("bearer "):
        return auth[7:].strip()
    return ""


@router.get(
    "/me/current-info",
    response_model=CurrentDeviceInfo,
    responses={401: {"model": ErrorResponse}},
)
async def current_device_info(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(require_active_user),
):
    """Return real-time device info for the current request (IP, browser, OS) plus matched DB records."""
    if not current_user.user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    token = _extract_token(request)
    info = await get_current_device_info(db, current_user.user_id, request, token)
    # Build Pydantic models from ORM objects — mark both as current
    device_out = DeviceOut.model_validate(info["device"]) if info["device"] else None
    if device_out:
        device_out.is_current = True
    session_out = UserSessionOut.model_validate(info["session"]) if info["session"] else None
    if session_out:
        session_out.is_current = True
    return CurrentDeviceInfo(
        ip=info["ip"],
        browser=info["browser"],
        os=info["os"],
        user_agent=info["user_agent"],
        fingerprint=info["fingerprint"],
        device_id=info["device_id"],
        session_id=info["session_id"],
        device=device_out,
        session=session_out,
    )


@router.get(
    "/me",
    response_model=list[DeviceOut],
    responses={401: {"model": ErrorResponse}},
)
async def my_devices(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(require_active_user),
):
    if not current_user.user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    ua = request.headers.get("User-Agent", "")
    ip = _get_client_ip(request)
    current_fp = _make_fingerprint(current_user.user_id, ua, ip)
    devices = await get_devices_for_user(db, current_user.user_id)
    out = []
    for d in devices:
        row = DeviceOut.model_validate(d)
        row.is_current = (d.device_fingerprint == current_fp)
        out.append(row)
    return out


@router.get(
    "/me/sessions",
    response_model=list[UserSessionOut],
    responses={401: {"model": ErrorResponse}},
)
async def my_sessions(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(require_active_user),
):
    if not current_user.user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    token = _extract_token(request)
    current_hash = _hash(token) if token else None
    sessions = await get_sessions_for_user(db, current_user.user_id)
    out = []
    for s in sessions:
        row = UserSessionOut.model_validate(s)
        row.is_current = bool(current_hash and s.session_token_hash == current_hash)
        out.append(row)
    return out


@router.get(
    "/me/events",
    response_model=list[DeviceEventOut],
    responses={401: {"model": ErrorResponse}},
)
async def my_device_events(
    limit: int = Query(default=50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(require_active_user),
):
    if not current_user.user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    return await get_device_events_for_user(db, current_user.user_id, limit=limit)


@router.post(
    "/sessions/{session_id}/revoke",
    response_model=MessageResponse,
    responses={401: {"model": ErrorResponse}, 404: {"model": ErrorResponse}},
)
async def revoke_my_session(
    session_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(require_active_user),
):
    if not current_user.user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    session = await revoke_session(db, session_id, user_id=current_user.user_id)
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    await db.commit()
    return {"message": "Session revoked."}


# ── Admin endpoints ───────────────────────────────────────────────────────────

@router.get(
    "/admin",
    response_model=list[DeviceAdminOut],
    responses={401: {"model": ErrorResponse}, 403: {"model": ErrorResponse}},
)
async def all_devices(
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(require_admin),
):
    return await get_all_devices(db)


@router.get(
    "/admin/events",
    response_model=list[DeviceEventOut],
    responses={401: {"model": ErrorResponse}, 403: {"model": ErrorResponse}},
)
async def all_device_events(
    limit: int = Query(default=200, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(require_admin),
):
    return await get_all_device_events(db, limit=limit)


@router.post(
    "/{device_id}/trust",
    response_model=DeviceAdminOut,
    responses={401: {"model": ErrorResponse}, 403: {"model": ErrorResponse}, 404: {"model": ErrorResponse}},
)
async def update_device_trust(
    device_id: int,
    body: DeviceTrustUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(require_admin),
):
    device = await set_device_trust(db, device_id, body.status, body.trust_score, body.reason)
    if not device:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")
    await db.commit()
    return device


@router.post(
    "/{device_id}/revoke",
    response_model=MessageResponse,
    responses={401: {"model": ErrorResponse}, 403: {"model": ErrorResponse}, 404: {"model": ErrorResponse}},
)
async def admin_revoke_device(
    device_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(require_admin),
):
    device = await revoke_device(db, device_id, admin_id=current_user.user_id)
    if not device:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")
    await db.commit()
    return {"message": f"Device {device_id} revoked."}
