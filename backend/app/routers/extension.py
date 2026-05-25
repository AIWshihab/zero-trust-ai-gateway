import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import get_db
from app.core.security import create_access_token, require_active_user
from app.models.device import Device
from app.models.extension import ExtensionPairingToken
from app.models.user import User
from app.schemas import TokenData
from app.schemas.extension import (
    ExtensionPairingTokenResponse,
    ExtensionRegisterDeviceRequest,
    ExtensionRegisterDeviceResponse,
    ExtensionSetupSessionResponse,
)
from app.services.device_service import _hash, create_session, emit_device_event

router = APIRouter()


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _token_hash(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _gateway_api_base_url(request: Request) -> str:
    configured = get_settings().PUBLIC_GATEWAY_API_URL or get_settings().FRONTEND_ORIGIN
    if configured:
        return configured.rstrip("/")
    return str(request.base_url).rstrip("/")


def _aware_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _connect_url(request: Request, token: str, setup_session_id: str) -> str:
    base = str(request.base_url).rstrip("/")
    gateway = _gateway_api_base_url(request)
    return (
        f"{base}/dashboard/extension/connect"
        f"?token={token}&gateway_api_url={gateway}&setup_session_id={setup_session_id}"
    )


def _setup_status(row: ExtensionPairingToken, device: Device | None, now: datetime) -> str:
    if row.is_revoked or (device is not None and (device.is_revoked or device.status == "revoked")):
        return "revoked"
    if row.connected_at and row.registered_device_id:
        return "connected"
    if _aware_utc(row.expires_at) <= now:
        return "expired"
    return "waiting_for_connection"


def _setup_response(
    row: ExtensionPairingToken,
    request: Request,
    status_value: str,
    token: str | None = None,
    device: Device | None = None,
) -> ExtensionSetupSessionResponse:
    settings = get_settings()
    connect_token = token or ""
    return ExtensionSetupSessionResponse(
        setup_session_id=row.setup_session_id,
        status=status_value,
        expires_at=row.expires_at,
        gateway_api_base_url=_gateway_api_base_url(request),
        connect_url=_connect_url(request, connect_token, row.setup_session_id) if connect_token else "",
        chrome_extension_store_url=settings.CHROME_EXTENSION_STORE_URL,
        extension_id=settings.EXTENSION_ID,
        device_id=row.registered_device_id,
        browser_name=row.browser_name or (device.browser if device else None),
        extension_version=row.extension_version,
        last_connected_at=row.connected_at or (device.last_seen if device else None),
    )


@router.post("/pairing-token", response_model=ExtensionPairingTokenResponse)
async def create_pairing_token(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(require_active_user),
):
    token = f"zta_pair_{secrets.token_urlsafe(24)}"
    setup_session_id = f"zta_setup_{secrets.token_urlsafe(18)}"
    expires_at = _utc_now() + timedelta(minutes=10)
    row = ExtensionPairingToken(
        user_id=current_user.user_id,
        token_hash=_token_hash(token),
        setup_session_id=setup_session_id,
        expires_at=expires_at,
        is_revoked=False,
    )
    db.add(row)
    await db.commit()
    return ExtensionPairingTokenResponse(
        token=token,
        expires_at=expires_at,
        gateway_api_base_url=_gateway_api_base_url(request),
        setup_session_id=setup_session_id,
        connect_url=_connect_url(request, token, setup_session_id),
        chrome_extension_store_url=get_settings().CHROME_EXTENSION_STORE_URL,
        extension_id=get_settings().EXTENSION_ID,
    )


@router.post("/setup-session", response_model=ExtensionSetupSessionResponse)
async def create_setup_session(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(require_active_user),
):
    token = f"zta_pair_{secrets.token_urlsafe(24)}"
    setup_session_id = f"zta_setup_{secrets.token_urlsafe(18)}"
    expires_at = _utc_now() + timedelta(minutes=10)
    row = ExtensionPairingToken(
        user_id=current_user.user_id,
        token_hash=_token_hash(token),
        setup_session_id=setup_session_id,
        expires_at=expires_at,
        is_revoked=False,
    )
    db.add(row)
    await db.commit()
    return _setup_response(row, request, "waiting_for_connection", token=token)


@router.get("/setup-session/{setup_session_id}", response_model=ExtensionSetupSessionResponse)
async def get_setup_session(
    setup_session_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(require_active_user),
):
    row = (
        await db.execute(
            select(ExtensionPairingToken).where(
                ExtensionPairingToken.setup_session_id == setup_session_id,
                ExtensionPairingToken.user_id == current_user.user_id,
            )
        )
    ).scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Extension setup session not found")

    device = None
    if row.registered_device_id:
        device = (await db.execute(select(Device).where(Device.id == row.registered_device_id))).scalar_one_or_none()
    status_value = _setup_status(row, device, _utc_now())
    return _setup_response(row, request, status_value, device=device)


@router.post("/register-device", response_model=ExtensionRegisterDeviceResponse)
async def register_extension_device(
    payload: ExtensionRegisterDeviceRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    now = _utc_now()
    row = (
        await db.execute(
            select(ExtensionPairingToken).where(
                ExtensionPairingToken.token_hash == _token_hash(payload.pairing_token)
            )
        )
    ).scalar_one_or_none()
    if row is None or row.is_revoked or row.used_at is not None or _aware_utc(row.expires_at) <= now:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired pairing token")
    if payload.setup_session_id and row.setup_session_id != payload.setup_session_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Pairing token does not match setup session")

    user = (await db.execute(select(User).where(User.id == row.user_id))).scalar_one_or_none()
    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Pairing user is no longer active")

    fingerprint_raw = "|".join(
        [
            str(user.id),
            payload.browser_name,
            payload.extension_version,
            payload.platform,
            payload.timezone,
            payload.user_agent[:200],
        ]
    )
    fingerprint = _hash(fingerprint_raw)
    existing = (
        await db.execute(
            select(Device).where(
                Device.user_id == user.id,
                Device.device_fingerprint == fingerprint,
            )
        )
    ).scalar_one_or_none()

    if existing is None:
        device = Device(
            user_id=user.id,
            device_fingerprint=fingerprint,
            device_name=payload.device_label or f"{payload.browser_name} extension",
            browser=payload.browser_name,
            os=payload.platform or "Browser",
            user_agent_hash=_hash(payload.user_agent or "browser_extension"),
            ip_hash=_hash(request.client.host if request.client else "unknown"),
            trust_score=55.0,
            risk_level="medium",
            status="new",
            login_count=1,
            failed_attempts=0,
            is_revoked=False,
            first_seen=now,
            last_seen=now,
        )
        db.add(device)
        await db.flush()
    else:
        device = existing
        if device.is_revoked:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="This extension device is revoked")
        device.last_seen = now
        device.login_count = (device.login_count or 0) + 1
        device.browser = payload.browser_name
        device.os = payload.platform or device.os
        device.device_name = payload.device_label or device.device_name
        device.user_agent_hash = _hash(payload.user_agent or "browser_extension")

    scopes = ["user", "browser_extension"]
    if user.is_admin:
        scopes.append("admin")
    expires_delta = timedelta(minutes=get_settings().ACCESS_TOKEN_EXPIRE_MINUTES)
    expires_at = now + expires_delta
    access_token = create_access_token(
        data={
            "sub": user.username,
            "uid": user.id,
            "email": user.email,
            "username": user.username,
            "scopes": scopes,
            "device_id": device.id,
            "client": "browser_extension",
        },
        expires_delta=expires_delta,
    )
    session = await create_session(db, user.id, device, access_token, request, expires_at)
    row.used_at = now
    row.registered_device_id = device.id
    row.connected_at = now
    row.browser_name = payload.browser_name
    row.extension_version = payload.extension_version

    await emit_device_event(
        db,
        event_type="browser_extension_paired",
        user_id=user.id,
        username=user.username,
        device=device,
        session=session,
        severity="info",
        explanation="Browser extension paired with the Zero Trust AI Gateway.",
        source_module="browser_extension",
        metadata={
            "route": "/api/v1/extension/register-device",
            "source": "browser_extension",
            "extension_version": payload.extension_version,
            "browser_name": payload.browser_name,
            "user_agent": payload.user_agent[:300],
            "timezone": payload.timezone,
            "platform": payload.platform,
            "device_label": payload.device_label,
            "timestamp": now.isoformat(),
        },
    )
    await db.commit()

    return ExtensionRegisterDeviceResponse(
        access_token=access_token,
        expires_in=get_settings().ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        device_id=device.id,
        gateway_api_base_url=_gateway_api_base_url(request),
    )
