import json
import secrets
from uuid import uuid4

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import require_admin
from app.models.firewall import FirewallClient
from app.routers.gateway import _messages_to_prompt, _run_gateway_pipeline
from app.schemas import (
    FirewallClientCreate,
    FirewallClientOut,
    FirewallClientUpdate,
    FirewallProxyResponse,
    GatewayInterceptRequest,
    TokenData,
)
from app.services.firewall_clients import (
    authenticate_firewall_client,
    check_client_rate_limit,
    hash_api_key,
    update_client_trust,
    verify_request_signature,
)

router = APIRouter()


def _client_out(row: FirewallClient, api_key: str | None = None) -> FirewallClientOut:
    return FirewallClientOut(
        id=row.id,
        client_id=row.client_id,
        name=row.name,
        rate_limit=row.rate_limit,
        rate_window_seconds=row.rate_window_seconds,
        trust_score=row.trust_score,
        require_signature=row.require_signature,
        is_active=row.is_active,
        created_at=row.created_at.isoformat() if row.created_at else None,
        updated_at=row.updated_at.isoformat() if row.updated_at else None,
        api_key=api_key,
    )


@router.get("/clients", response_model=list[FirewallClientOut])
async def list_firewall_clients(
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(require_admin),
):
    rows = (await db.execute(select(FirewallClient).order_by(FirewallClient.created_at.desc()))).scalars().all()
    return [_client_out(row) for row in rows]


@router.post("/clients", response_model=FirewallClientOut, status_code=status.HTTP_201_CREATED)
async def create_firewall_client(
    payload: FirewallClientCreate,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(require_admin),
):
    existing = (
        await db.execute(select(FirewallClient).where(FirewallClient.client_id == payload.client_id))
    ).scalar_one_or_none()
    if existing is not None:
        raise HTTPException(status_code=409, detail="Firewall client already exists")

    api_key = payload.api_key or f"gw_{secrets.token_urlsafe(24)}"
    row = FirewallClient(
        client_id=payload.client_id,
        name=payload.name,
        api_key_hash=hash_api_key(api_key),
        hmac_secret=payload.hmac_secret,
        require_signature=payload.require_signature,
        rate_limit=payload.rate_limit,
        rate_window_seconds=payload.rate_window_seconds,
        trust_score=payload.trust_score,
        is_active=payload.is_active,
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return _client_out(row, api_key=api_key)


@router.patch("/clients/{client_id}", response_model=FirewallClientOut)
async def update_firewall_client(
    client_id: str,
    payload: FirewallClientUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(require_admin),
):
    row = (
        await db.execute(select(FirewallClient).where(FirewallClient.client_id == client_id))
    ).scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="Firewall client not found")

    api_key = None
    for field in ("name", "rate_limit", "rate_window_seconds", "trust_score", "require_signature", "hmac_secret", "is_active"):
        value = getattr(payload, field)
        if value is not None:
            setattr(row, field, value)
    if payload.api_key:
        api_key = payload.api_key
        row.api_key_hash = hash_api_key(api_key)

    await db.commit()
    await db.refresh(row)
    return _client_out(row, api_key=api_key)


def _payload_from_json(body: bytes) -> GatewayInterceptRequest:
    try:
        data = json.loads(body.decode("utf-8") or "{}")
    except json.JSONDecodeError:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid JSON request body")
    return GatewayInterceptRequest.model_validate(data)


@router.post("/proxy", response_model=FirewallProxyResponse)
async def firewall_proxy(
    request: Request,
    db: AsyncSession = Depends(get_db),
    x_gateway_api_key: str | None = Header(default=None),
    x_gateway_signature: str | None = Header(default=None),
    x_gateway_timestamp: str | None = Header(default=None),
):
    body = await request.body()
    client = await authenticate_firewall_client(db, x_gateway_api_key)
    verify_request_signature(
        client,
        body=body,
        signature=x_gateway_signature,
        timestamp=x_gateway_timestamp,
    )

    rate = check_client_rate_limit(client)
    if not rate.allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "message": "Firewall client rate limit exceeded",
                "client_id": client.client_id,
                "retry_after_seconds": rate.retry_after_seconds,
                "rate": rate.__dict__,
            },
        )

    payload = _payload_from_json(body)
    trace_id = f"firewall-{uuid4().hex}"
    prompt = (payload.prompt or _messages_to_prompt(payload.messages)).strip()
    result = await _run_gateway_pipeline(
        db=db,
        model_ref=payload.model_id,
        prompt=prompt,
        messages=payload.messages,
        external_user_id=payload.external_user_id,
        client_id=payload.client_id or client.client_id,
        policy_context=payload.policy_context,
        parameters=payload.parameters,
        source="firewall_proxy",
        trace_id=trace_id,
        extra_gateway_context={
            "firewall_client_id": client.client_id,
            "firewall_client_db_id": client.id,
            "client_rate": rate.__dict__,
        },
    )

    update_client_trust(
        client,
        decision=result.decision.value if hasattr(result.decision, "value") else str(result.decision),
        effective_risk=result.effective_risk,
    )
    await db.commit()

    return FirewallProxyResponse(
        decision=result.decision,
        output=result.output,
        reason=result.reason,
        effective_risk=result.effective_risk,
        trace_id=trace_id,
        forwarded=bool(result.forwarded),
        factors=result.factors,
        explanation=result.explanation,
        decision_trace=result.decision_trace,
        client_id=client.client_id,
        rate=rate.__dict__,
    )
