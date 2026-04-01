from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from passlib.context import CryptContext
from app.models.user import User
from app.models.schemas import UserCreate
from app.core.security import hash_password

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

async def authenticate_user(db: AsyncSession, username: str, password: str) -> User | None:
    # Accept login by either username or email
    user = await get_user_by_username(db, username) or await get_user_by_email(db, username)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user

async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    result = await db.execute(select(User).where(User.email == email))
    return result.scalars().first()

async def get_user_by_username(db: AsyncSession, username: str) -> User | None:
    result = await db.execute(select(User).where(User.username == username))
    return result.scalars().first()

async def create_user(db: AsyncSession, data: UserCreate) -> User:
    user = User(
        email=data.email,
        username=data.username,
        hashed_password=hash_password(data.password),  # ← plain password only
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)
