"""Device trust + session intelligence service.

Handles device fingerprinting, trust scoring, SOC event emission,
and session lifecycle. All logic is production-safe: no localhost
assumptions, proper UTC timestamps, no raw secrets stored.
"""

import hashlib
import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.device import Device
from app.models.device_event import DeviceEvent
from app.models.user_session import UserSession

logger = logging.getLogger(__name__)

USER_MODEL_LIMIT = 3


# ── Helpers ──────────────────────────────────────────────────────────────────

def _hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:32]


def _get_client_ip(request: Request) -> str:
    """Extract real IP respecting reverse proxy headers."""
    xff = request.headers.get("X-Forwarded-For", "")
    if xff:
        return xff.split(",")[0].strip()
    xrp = request.headers.get("X-Real-IP", "")
    if xrp:
        return xrp.strip()
    if request.client:
        return request.client.host or "unknown"
    return "unknown"


def _parse_user_agent(ua: str) -> tuple[str, str]:
    """Return (browser, os) strings from user-agent without external deps."""
    ua_lower = ua.lower()

    # Browser detection
    if "edg/" in ua_lower or "edge/" in ua_lower:
        browser = "Edge"
    elif "opr/" in ua_lower or "opera" in ua_lower:
        browser = "Opera"
    elif "chrome/" in ua_lower and "chromium" not in ua_lower:
        browser = "Chrome"
    elif "firefox/" in ua_lower:
        browser = "Firefox"
    elif "safari/" in ua_lower and "chrome" not in ua_lower:
        browser = "Safari"
    elif "msie" in ua_lower or "trident/" in ua_lower:
        browser = "Internet Explorer"
    else:
        browser = "Unknown"

    # OS detection
    if "windows nt 10" in ua_lower:
        os_name = "Windows 10/11"
    elif "windows nt" in ua_lower:
        os_name = "Windows"
    elif "mac os x" in ua_lower or "macos" in ua_lower:
        os_name = "macOS"
    elif "iphone" in ua_lower or "ipad" in ua_lower:
        os_name = "iOS"
    elif "android" in ua_lower:
        os_name = "Android"
    elif "linux" in ua_lower:
        os_name = "Linux"
    else:
        os_name = "Unknown"

    return browser, os_name


def _make_fingerprint(user_id: int, ua: str, ip: str) -> str:
    """Stable device fingerprint from user+UA+IP prefix."""
    ip_prefix = ".".join(ip.split(".")[:3]) if "." in ip else ip
    raw = f"{user_id}|{ua[:200]}|{ip_prefix}"
    return _hash(raw)


def _compute_trust_score(device: Device) -> tuple[float, str]:
    """Return (trust_score 0-100, risk_level)."""
    score = device.trust_score

    # Reward repeated successful logins
    score = min(100.0, score + min(device.login_count * 2.0, 20.0))

    # Penalise failed attempts
    score = max(0.0, score - device.failed_attempts * 10.0)

    # New device penalty
    if device.status == "new":
        score = min(score, 65.0)

    if score >= 80:
        risk = "low"
    elif score >= 55:
        risk = "medium"
    elif score >= 30:
        risk = "high"
    else:
        risk = "critical"

    return round(score, 1), risk


# ── Core device operations ────────────────────────────────────────────────────

async def get_or_create_device(
    db: AsyncSession,
    user_id: int,
    username: str,
    request: Request,
) -> tuple[Device, bool]:
    """Return (device, is_new). Creates or updates device record."""
    ua = request.headers.get("User-Agent", "")
    ip = _get_client_ip(request)
    fp = _make_fingerprint(user_id, ua, ip)
    browser, os_name = _parse_user_agent(ua)

    result = await db.execute(
        select(Device).where(Device.user_id == user_id, Device.device_fingerprint == fp)
    )
    device = result.scalars().first()
    is_new = device is None

    now = datetime.now(timezone.utc)

    if is_new:
        device = Device(
            user_id=user_id,
            device_fingerprint=fp,
            device_name=f"{browser} on {os_name}",
            browser=browser,
            os=os_name,
            user_agent_hash=_hash(ua),
            ip_hash=_hash(ip),
            trust_score=60.0,
            risk_level="medium",
            status="new",
            login_count=1,
            failed_attempts=0,
            is_revoked=False,
            first_seen=now,
            last_seen=now,
        )
        db.add(device)
    else:
        device.login_count = (device.login_count or 0) + 1
        device.last_seen = now
        device.browser = browser
        device.os = os_name
        device.user_agent_hash = _hash(ua)
        device.ip_hash = _hash(ip)
        # Graduate "new" to "trusted" after 3+ successful logins
        if device.status == "new" and (device.login_count or 0) >= 3:
            device.status = "trusted"

    new_score, new_risk = _compute_trust_score(device)
    device.trust_score = new_score
    device.risk_level = new_risk

    await db.flush()
    return device, is_new


async def create_session(
    db: AsyncSession,
    user_id: int,
    device: Device,
    token: str,
    request: Request,
    expires_at: Optional[datetime] = None,
) -> UserSession:
    """Create a new session record tied to user + device."""
    ua = request.headers.get("User-Agent", "")
    ip = _get_client_ip(request)
    now = datetime.now(timezone.utc)

    session = UserSession(
        user_id=user_id,
        device_id=device.id,
        session_token_hash=_hash(token),
        ip_hash=_hash(ip),
        user_agent=ua[:512],
        is_active=True,
        created_at=now,
        last_active_at=now,
        expires_at=expires_at,
    )
    db.add(session)
    await db.flush()
    return session


async def emit_device_event(
    db: AsyncSession,
    event_type: str,
    user_id: Optional[int],
    username: Optional[str],
    device: Optional[Device],
    session: Optional[UserSession],
    severity: str = "info",
    explanation: str = "",
    source_module: str = "auth",
    metadata: Optional[dict] = None,
) -> None:
    """Write a SOC device event row."""
    risk_map = {"info": "low", "warning": "medium", "high": "high", "critical": "critical"}
    event = DeviceEvent(
        event_type=event_type,
        user_id=user_id,
        username_snapshot=username,
        device_id=device.id if device else None,
        session_id=session.id if session else None,
        browser=device.browser if device else None,
        os=device.os if device else None,
        ip_hash=device.ip_hash if device else None,
        severity=severity,
        risk_level=risk_map.get(severity, "low"),
        source_module=source_module,
        explanation=explanation,
        metadata_json=metadata or {},
        timestamp=datetime.now(timezone.utc),
    )
    db.add(event)


async def process_login(
    db: AsyncSession,
    user_id: int,
    username: str,
    token: str,
    request: Request,
    token_expires_at: Optional[datetime] = None,
) -> tuple[Device, UserSession]:
    """Main entry called after successful authentication.

    Creates/updates device, creates session, emits SOC events.
    All DB writes committed by caller.
    """
    device, is_new = await get_or_create_device(db, user_id, username, request)
    session = await create_session(db, user_id, device, token, request, token_expires_at)

    if is_new:
        await emit_device_event(
            db,
            event_type="new_device_login",
            user_id=user_id,
            username=username,
            device=device,
            session=session,
            severity="warning",
            explanation=f"First login from this device ({device.browser} on {device.os}).",
            source_module="auth",
            metadata={"browser": device.browser, "os": device.os},
        )
    else:
        await emit_device_event(
            db,
            event_type="device_seen",
            user_id=user_id,
            username=username,
            device=device,
            session=session,
            severity="info",
            explanation=f"Known device login #{device.login_count}.",
            source_module="auth",
        )

    # Flag high-risk logins
    if device.risk_level in ("high", "critical"):
        await emit_device_event(
            db,
            event_type="suspicious_device_change",
            user_id=user_id,
            username=username,
            device=device,
            session=session,
            severity="high",
            explanation=f"Login flagged: device risk level is {device.risk_level} (score {device.trust_score}).",
            source_module="auth",
            metadata={"risk_level": device.risk_level, "trust_score": device.trust_score},
        )

    return device, session


# ── Admin / query helpers ─────────────────────────────────────────────────────

async def get_current_device_info(
    db: AsyncSession,
    user_id: int,
    request: Request,
    token: Optional[str] = None,
) -> dict:
    """Return live device info for the current request plus matched DB records."""
    ua = request.headers.get("User-Agent", "")
    ip = _get_client_ip(request)
    browser, os_name = _parse_user_agent(ua)
    fp = _make_fingerprint(user_id, ua, ip)

    device_row = None
    session_row = None

    # Match device by fingerprint
    dev_result = await db.execute(
        select(Device).where(Device.user_id == user_id, Device.device_fingerprint == fp)
    )
    device_row = dev_result.scalars().first()

    # Match session by token hash
    if token:
        token_hash = _hash(token)
        sess_result = await db.execute(
            select(UserSession).where(
                UserSession.user_id == user_id,
                UserSession.session_token_hash == token_hash,
            )
        )
        session_row = sess_result.scalars().first()

    return {
        "ip": ip,
        "browser": browser,
        "os": os_name,
        "user_agent": ua[:300] if ua else "",
        "fingerprint": fp,
        "device_id": device_row.id if device_row else None,
        "session_id": session_row.id if session_row else None,
        "device": device_row,
        "session": session_row,
    }


async def get_devices_for_user(db: AsyncSession, user_id: int) -> list[Device]:
    result = await db.execute(
        select(Device).where(Device.user_id == user_id).order_by(Device.last_seen.desc())
    )
    return list(result.scalars().all())


async def get_all_devices(db: AsyncSession) -> list[Device]:
    result = await db.execute(select(Device).order_by(Device.last_seen.desc()))
    return list(result.scalars().all())


async def get_sessions_for_user(db: AsyncSession, user_id: int) -> list[UserSession]:
    result = await db.execute(
        select(UserSession).where(UserSession.user_id == user_id).order_by(UserSession.created_at.desc())
    )
    return list(result.scalars().all())


async def get_device_events_for_user(db: AsyncSession, user_id: int, limit: int = 50) -> list[DeviceEvent]:
    result = await db.execute(
        select(DeviceEvent).where(DeviceEvent.user_id == user_id)
        .order_by(DeviceEvent.timestamp.desc()).limit(limit)
    )
    return list(result.scalars().all())


async def get_all_device_events(db: AsyncSession, limit: int = 200) -> list[DeviceEvent]:
    result = await db.execute(
        select(DeviceEvent).order_by(DeviceEvent.timestamp.desc()).limit(limit)
    )
    return list(result.scalars().all())


async def revoke_device(
    db: AsyncSession, device_id: int, admin_id: Optional[int] = None
) -> Optional[Device]:
    result = await db.execute(select(Device).where(Device.id == device_id))
    device = result.scalars().first()
    if not device:
        return None
    device.is_revoked = True
    device.status = "revoked"
    device.trust_score = 0.0
    device.risk_level = "critical"
    await emit_device_event(
        db,
        event_type="device_revoked",
        user_id=device.user_id,
        username=None,
        device=device,
        session=None,
        severity="critical",
        explanation="Device revoked by administrator.",
        source_module="admin",
        metadata={"admin_id": admin_id},
    )
    return device


async def set_device_trust(
    db: AsyncSession, device_id: int, status: str, trust_score: Optional[float], reason: Optional[str]
) -> Optional[Device]:
    result = await db.execute(select(Device).where(Device.id == device_id))
    device = result.scalars().first()
    if not device:
        return None
    device.status = status
    if trust_score is not None:
        device.trust_score = trust_score
    if status == "trusted":
        device.risk_level = "low"
        device.is_revoked = False
    elif status == "revoked":
        device.is_revoked = True
        device.risk_level = "critical"
        device.trust_score = 0.0
    _, new_risk = _compute_trust_score(device)
    if status not in ("trusted", "revoked"):
        device.risk_level = new_risk
    await emit_device_event(
        db,
        event_type="device_trust_updated",
        user_id=device.user_id,
        username=None,
        device=device,
        session=None,
        severity="warning" if status in ("suspicious", "revoked") else "info",
        explanation=reason or f"Device status set to {status}.",
        source_module="admin",
    )
    return device


async def revoke_session(db: AsyncSession, session_id: int, user_id: Optional[int] = None) -> Optional[UserSession]:
    q = select(UserSession).where(UserSession.id == session_id)
    if user_id is not None:
        q = q.where(UserSession.user_id == user_id)
    result = await db.execute(q)
    session = result.scalars().first()
    if not session:
        return None
    session.is_active = False
    session.revoked_at = datetime.now(timezone.utc)
    await emit_device_event(
        db,
        event_type="session_revoked",
        user_id=session.user_id,
        username=None,
        device=None,
        session=session,
        severity="warning",
        explanation="Session revoked.",
        source_module="auth",
    )
    return session


async def count_user_models(db: AsyncSession, user_id: int) -> int:
    """Count active user-owned models for limit enforcement."""
    from sqlalchemy import func
    from app.models.model import Model
    result = await db.execute(
        select(func.count()).where(Model.owner_user_id == user_id, Model.is_active == True)
    )
    return result.scalar() or 0
