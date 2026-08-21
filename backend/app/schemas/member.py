import uuid
from datetime import date, datetime

from pydantic import BaseModel, EmailStr

from app.models.backlog_item import BacklogItemStatus, BacklogItemType
from app.models.user import UserRole


class SkillStatOut(BaseModel):
    skill: str
    completed_task_count: int
    completed_story_points: int

    model_config = {"from_attributes": True}


class MemberOut(BaseModel):
    id: uuid.UUID
    email: EmailStr
    full_name: str | None
    role: UserRole
    skills: list[str]
    skill_stats: list[SkillStatOut] = []


class MemberSelfUpdate(BaseModel):
    full_name: str | None = None
    skills: list[str] | None = None


class MemberAdminUpdate(BaseModel):
    full_name: str | None = None
    skills: list[str] | None = None
    role: UserRole | None = None


class AssignedItemOut(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    project_name: str
    title: str
    item_type: BacklogItemType
    status: BacklogItemStatus
    story_points: int | None
    deadline: date | None
    updated_at: datetime

    model_config = {"from_attributes": True}
