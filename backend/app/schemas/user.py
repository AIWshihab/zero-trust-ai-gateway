from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6)


class UserResponse(BaseModel):
    id: int
    email: str
    username: str
    is_admin: bool
    is_active: bool
    trust_score: float
    created_at: datetime

    model_config = {"from_attributes": True}
