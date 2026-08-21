import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field

from app.models.invite import InviteStatus
from app.models.user import UserRole
from app.schemas.auth import TokenResponse

__all__ = ["TokenResponse"]


class InviteCreate(BaseModel):
    email: EmailStr
    role: UserRole = UserRole.MEMBER


class InviteOut(BaseModel):
    id: uuid.UUID
    email: EmailStr
    role: UserRole
    status: InviteStatus
    accept_url: str
    created_at: datetime

    model_config = {"from_attributes": True}


class InvitePreview(BaseModel):
    org_name: str
    email: EmailStr


class InviteAcceptRequest(BaseModel):
    password: str = Field(min_length=8, max_length=255)
