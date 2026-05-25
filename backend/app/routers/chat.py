from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import require_active_user
from app.models.chat import ChatMessage, ChatSession
from app.schemas.chat import ChatMessageOut, ChatSessionCreate, ChatSessionOut, ChatSessionUpdate
from app.schemas import TokenData

router = APIRouter()


async def _get_owned_session(db: AsyncSession, session_id: int, current_user: TokenData) -> ChatSession:
    row = (
        await db.execute(
            select(ChatSession).where(
                ChatSession.id == session_id,
                ChatSession.user_id == current_user.user_id,
            )
        )
    ).scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat session not found")
    return row


async def _session_out(db: AsyncSession, session: ChatSession) -> ChatSessionOut:
    messages = (
        await db.execute(
            select(ChatMessage)
            .where(ChatMessage.session_id == session.id)
            .order_by(ChatMessage.created_at.asc(), ChatMessage.id.asc())
        )
    ).scalars().all()
    return ChatSessionOut(
        id=session.id,
        title=session.title,
        model_id=session.model_id,
        created_at=session.created_at,
        updated_at=session.updated_at,
        messages=[ChatMessageOut.model_validate(message) for message in messages],
    )


@router.get("/sessions", response_model=list[ChatSessionOut])
async def list_chat_sessions(
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(require_active_user),
):
    rows = (
        await db.execute(
            select(ChatSession)
            .where(ChatSession.user_id == current_user.user_id)
            .order_by(ChatSession.updated_at.desc(), ChatSession.id.desc())
        )
    ).scalars().all()
    return [await _session_out(db, row) for row in rows]


@router.post("/sessions", response_model=ChatSessionOut, status_code=status.HTTP_201_CREATED)
async def create_chat_session(
    payload: ChatSessionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(require_active_user),
):
    title = (payload.title or "New chat").strip()[:200] or "New chat"
    row = ChatSession(user_id=current_user.user_id, title=title, model_id=payload.model_id)
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return await _session_out(db, row)


@router.get("/sessions/{session_id}", response_model=ChatSessionOut)
async def get_chat_session(
    session_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(require_active_user),
):
    row = await _get_owned_session(db, session_id, current_user)
    return await _session_out(db, row)


@router.patch("/sessions/{session_id}", response_model=ChatSessionOut)
async def update_chat_session(
    session_id: int,
    payload: ChatSessionUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(require_active_user),
):
    row = await _get_owned_session(db, session_id, current_user)
    if payload.title is not None:
        row.title = payload.title.strip()[:200] or row.title
    if payload.model_id is not None:
        row.model_id = payload.model_id
    await db.commit()
    await db.refresh(row)
    return await _session_out(db, row)


@router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_chat_session(
    session_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(require_active_user),
):
    row = await _get_owned_session(db, session_id, current_user)
    await db.execute(delete(ChatMessage).where(ChatMessage.session_id == row.id))
    await db.delete(row)
    await db.commit()
