from __future__ import annotations

import hashlib
import hmac
import time
from collections import defaultdict, deque
from dataclasses import dataclass

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.firewall import FirewallClient

DEFAULT_CLIENT_ID = "default-client"
DEFAULT_CLIENT_NAME = "Default Gateway Client"
DEFAULT_CLIENT_API_KEY = "key1"

_client_request_history: dict[str, deque[float]] = defaultdict(lambda: deque(maxlen=5000))


@dataclass(frozen=True)
class FirewallRateResult:
    allowed: bool
    requests_in_window: int
    limit: int
    window_seconds: int
    rate_score: float
    retry_after_seconds: int = 0


def hash_api_key(api_key: str) -> str:
    return hashlib.sha256(str(api_key).encode("utf-8")).hexdigest()


def _now() -> float:
    return time.time()


def _prune(client_id: str, window_seconds: int) -> None:
    cutoff = _now() - max(1, int(window_seconds))
    history = _client_request_history[client_id]
    while history and history[0] < cutoff:
        history.popleft()


async def seed_default_firewall_client(db: AsyncSession) -> FirewallClient:
    api_key_hash = hash_api_key(DEFAULT_CLIENT_API_KEY)
    row = (
        await db.execute(select(FirewallClient).where(FirewallClient.client_id == DEFAULT_CLIENT_ID))
    ).scalar_one_or_none()
    if row is not None:
        return row

    row = FirewallClient(
        client_id=DEFAULT_CLIENT_ID,
        name=DEFAULT_CLIENT_NAME,
        api_key_hash=api_key_hash,
        rate_limit=60,
        rate_window_seconds=60,
        trust_score=0.8,
        is_active=True,
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return row


async def authenticate_firewall_client(db: AsyncSession, api_key: str | None) -> FirewallClient:
    if not api_key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing firewall API key")

    api_key_hash = hash_api_key(api_key)
    row = (
        await db.execute(select(FirewallClient).where(FirewallClient.api_key_hash == api_key_hash))
    ).scalar_one_or_none()

    if row is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid firewall API key")
    if not bool(row.is_active):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Firewall client is inactive")
    return row


def verify_request_signature(
    client: FirewallClient,
    *,
    body: bytes,
    signature: str | None,
    timestamp: str | None,
    max_skew_seconds: int = 300,
) -> None:
    if not bool(client.require_signature):
        return
    if not client.hmac_secret:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Client signing is required but no signing secret is configured")
    if not signature or not timestamp:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing request signature")

    try:
        signed_at = int(timestamp)
    except (TypeError, ValueError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid request signature timestamp")

    if abs(int(_now()) - signed_at) > max_skew_seconds:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Request signature timestamp outside allowed window")

    payload = timestamp.encode("utf-8") + b"." + body
    expected = hmac.new(str(client.hmac_secret).encode("utf-8"), payload, hashlib.sha256).hexdigest()
    normalized = signature.replace("sha256=", "", 1)
    if not hmac.compare_digest(expected, normalized):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid request signature")


def check_client_rate_limit(client: FirewallClient) -> FirewallRateResult:
    client_id = str(client.client_id)
    limit = max(1, int(client.rate_limit or 60))
    window = max(1, int(client.rate_window_seconds or 60))
    _prune(client_id, window)

    history = _client_request_history[client_id]
    count = len(history)
    rate_score = min(1.0, count / float(limit))

    if count >= limit:
        oldest = history[0] if history else _now()
        retry_after = max(1, int(round((oldest + window) - _now())))
        return FirewallRateResult(
            allowed=False,
            requests_in_window=count,
            limit=limit,
            window_seconds=window,
            rate_score=1.0,
            retry_after_seconds=retry_after,
        )

    history.append(_now())
    return FirewallRateResult(
        allowed=True,
        requests_in_window=count + 1,
        limit=limit,
        window_seconds=window,
        rate_score=min(1.0, (count + 1) / float(limit)),
    )


def update_client_trust(client: FirewallClient, *, decision: str, effective_risk: float) -> float:
    current = max(0.0, min(1.0, float(client.trust_score or 0.8)))
    decision_value = str(decision or "").lower()
    risk = max(0.0, min(1.0, float(effective_risk or 0.0)))

    if decision_value == "allow" and risk < 0.25:
        current += 0.005
    elif decision_value == "challenge":
        current -= 0.025
    elif decision_value == "block":
        current -= 0.055
    if risk >= 0.75:
        current -= 0.025

    client.trust_score = round(max(0.0, min(1.0, current)), 4)
    return float(client.trust_score)
