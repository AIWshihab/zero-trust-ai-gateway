from typing import Any

from pydantic import BaseModel, Field


class MessageResponse(BaseModel):
    message: str


class ErrorDetail(BaseModel):
    code: str
    message: str
    context: dict[str, Any] = Field(default_factory=dict)


class ErrorResponse(BaseModel):
    detail: str | ErrorDetail
