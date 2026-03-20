from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta

from app.core.security import (
    verify_password,
    create_access_token,
    get_current_user,
)
from app.core.config import get_settings
from app.models.schemas import TokenResponse, TokenData

settings = get_settings()
router = APIRouter()


# ─── Fake User Store (swap for DB in Stage 4) ─────────────────────────────────

FAKE_USERS_DB = {
    "admin": {
        "username": "admin",
        "hashed_password": "$2a$12$CasEai7EVhGHANsxDW8UN.pb0I4MXydl6Op.pY6bNvqrvMrMMaHTq",  # hash of "admin123"
        "scopes": ["admin", "user"],
        "is_active": True,
    },
    "user": {
        "username": "user",
        "hashed_password": "$2a$12$CasEai7EVhGHANsxDW8UN.pb0I4MXydl6Op.pY6bNvqrvMrMMaHTq",  # hash of "user123"
        "scopes": ["user"],
        "is_active": True,
    },
}


def get_user(username: str) -> dict | None:
    return FAKE_USERS_DB.get(username)


def authenticate_user(username: str, password: str) -> dict | None:
    user = get_user(username)
    if not user:
        return None
    if not verify_password(password, user["hashed_password"]):
        return None
    return user


# ─── Generate Hashed Passwords (run once in terminal) ───────────────────────── python3 -c "from app.core.security import hash_password; print(hash_password('admin123')); print(hash_password('user123'))"
# from app.core.security import hash_password
# print(hash_password("admin123"))
# print(hash_password("user123"))
# Paste the outputs above into FAKE_USERS_DB



# ─── Routes ───────────────────────────────────────────────────────────────────

@router.post("/token", response_model=TokenResponse)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user["is_active"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled",
        )

    access_token = create_access_token(
        data={
            "sub": user["username"],
            "scopes": user["scopes"],
        },
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.get("/me", response_model=TokenData)
async def get_me(current_user: TokenData = Depends(get_current_user)):
    return current_user


@router.post("/logout")
async def logout():
    # JWT is stateless — instruct client to discard token
    return {"message": "Logged out successfully. Discard your token."}
