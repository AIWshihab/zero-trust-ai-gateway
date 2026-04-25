from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import get_db
from app.core.rate_limiter import get_rate_profile
from app.core.security import create_access_token, get_current_user, require_active_user
from app.schemas import ErrorResponse, MessageResponse, TokenData, TokenResponse, UserCreate, UserResponse
from app.services.user_service import (
    authenticate_user,
    create_user,
    get_user_by_email,
    get_user_by_username,
)
from app.services.reassessment_service import get_trust_profile_persistent

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
    scopes = ["user"]
    if user.is_admin:
        scopes.append("admin")

    payload = {
        "sub": user.username,
        "uid": user.id,
        "email": user.email,
        "username": user.username,
        "scopes": scopes,
    }
    access_token = create_access_token(
        data=payload,
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )

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
