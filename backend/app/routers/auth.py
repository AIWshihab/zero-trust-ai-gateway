from datetime import timedelta, timezone, datetime
import logging

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import get_db
from app.core.rate_limiter import get_rate_profile
from app.core.security import (
    create_access_token,
    get_current_user,
    hash_password,
    require_active_user,
    require_admin,
    verify_password,
)
from app.schemas import (
    AdminPasswordResetRequest,
    ErrorResponse,
    MessageResponse,
    PasswordChangeRequest,
    TokenData,
    TokenResponse,
    UserCreate,
    UserResponse,
)
from app.services.user_service import (
    authenticate_user,
    create_user,
    get_user_by_email,
    get_user_by_username,
)
from app.services.reassessment_service import get_trust_profile_persistent
from app.services.device_service import process_login

logger = logging.getLogger(__name__)

settings = get_settings()
router = APIRouter()


# ─── Signup ───────────────────────────────────────────────────────────────────


@router.post(
    "/signup",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        409: {"model": ErrorResponse, "description": "Email or username already exists"},
    },
)
async def signup(data: UserCreate, db: AsyncSession = Depends(get_db)):
    if data.username.lower() == "admin":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username reserved",
        )
    if await get_user_by_email(db, data.email):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )
    if await get_user_by_username(db, data.username):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already taken",
        )
    return await create_user(db, data)


# ─── Login ────────────────────────────────────────────────────────────────────


@router.post(
    "/token",
    response_model=TokenResponse,
    responses={
        401: {"model": ErrorResponse, "description": "Invalid credentials"},
        403: {"model": ErrorResponse, "description": "User account disabled"},
    },
)
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
):
    user = await authenticate_user(db, form_data.username, form_data.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled",
        )
    scopes = ["user", "admin"]

    expires_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    expires_at = datetime.now(timezone.utc) + expires_delta

    payload = {
        "sub": user.username,
        "uid": user.id,
        "email": user.email,
        "username": user.username,
        "scopes": scopes,
    }
    access_token = create_access_token(data=payload, expires_delta=expires_delta)

    # Device + session tracking (non-blocking — errors must not fail login)
    try:
        await process_login(
            db=db,
            user_id=int(user.id),
            username=str(user.username),
            token=access_token,
            request=request,
            token_expires_at=expires_at,
        )
        await db.commit()
    except Exception as exc:
        logger.warning("Device tracking failed for user %s: %s", user.username, exc)

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


# ─── Current User ─────────────────────────────────────────────────────────────


@router.get(
    "/me",
    response_model=TokenData,
    responses={401: {"model": ErrorResponse, "description": "Unauthorized"}},
)
async def get_me(current_user: TokenData = Depends(get_current_user)):
    return current_user


@router.get(
    "/me/profile",
    responses={401: {"model": ErrorResponse, "description": "Unauthorized"}},
)
async def get_my_profile(
    current_user: TokenData = Depends(require_active_user),
    db: AsyncSession = Depends(get_db),
):
    username = current_user.username
    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    trust_profile = await get_trust_profile_persistent(db, username)
    rate_profile = get_rate_profile(username)

    return {
        "user": current_user,
        "trust": trust_profile,
        "rate": rate_profile,
        "security_posture": {
            "status": "penalized" if rate_profile.get("penalty_active") else trust_profile.get("trust_level", "unknown"),
            "can_use_models": not bool(rate_profile.get("penalty_active")),
            "cooldown_remaining_seconds": rate_profile.get("cooldown_remaining_seconds", 0),
        },
    }


# ─── Logout ───────────────────────────────────────────────────────────────────


@router.post("/logout", response_model=MessageResponse)
async def logout():
    # JWT is stateless — instruct client to discard token
    return {"message": "Logged out successfully. Discard your token."}


@router.post(
    "/me/change-password",
    response_model=MessageResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid password change request"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
    },
)
async def change_my_password(
    data: PasswordChangeRequest,
    current_user: TokenData = Depends(require_active_user),
    db: AsyncSession = Depends(get_db),
):
    user = await get_user_by_username(db, current_user.username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User no longer exists",
        )

    if not verify_password(data.current_password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )

    if data.current_password == data.new_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be different from current password",
        )

    user.hashed_password = hash_password(data.new_password)
    await db.commit()
    return {"message": "Password updated successfully."}


@router.post(
    "/admin/reset-password",
    response_model=MessageResponse,
    responses={
        403: {"model": ErrorResponse, "description": "Admin access required"},
        404: {"model": ErrorResponse, "description": "User not found"},
    },
)
async def admin_reset_password(
    data: AdminPasswordResetRequest,
    _: TokenData = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    user = await get_user_by_username(db, data.username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    user.hashed_password = hash_password(data.new_password)
    await db.commit()
    return {"message": f"Password reset for user '{user.username}'."}
