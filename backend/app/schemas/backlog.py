import uuid
from datetime import date, datetime

from pydantic import BaseModel, Field

from app.models.backlog_item import BacklogItemStatus, BacklogItemType


class BacklogItemCreate(BaseModel):
    title: str = Field(min_length=1, max_length=500)
    description: str | None = None
    impact_score: float | None = None
    deadline: date | None = None
    item_type: BacklogItemType = BacklogItemType.TASK
    parent_id: uuid.UUID | None = None
    story_points: int | None = None
    required_skills: list[str] = Field(default_factory=list)
    acceptance_criteria: str | None = None
    assignee_id: uuid.UUID | None = None


class BacklogItemUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    status: BacklogItemStatus | None = None
    impact_score: float | None = None
    deadline: date | None = None
    priority_rank: int | None = None
    sprint_id: uuid.UUID | None = None
    item_type: BacklogItemType | None = None
    parent_id: uuid.UUID | None = None
    story_points: int | None = None
    required_skills: list[str] | None = None
    acceptance_criteria: str | None = None
    assignee_id: uuid.UUID | None = None


class BacklogItemOut(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    sprint_id: uuid.UUID | None
    parent_id: uuid.UUID | None
    assignee_id: uuid.UUID | None
    title: str
    description: str | None
    status: BacklogItemStatus
    item_type: BacklogItemType
    impact_score: float | None
    deadline: date | None
    priority_rank: int | None
    story_points: int | None
    required_skills: list[str]
    acceptance_criteria: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class BacklogTreeNode(BacklogItemOut):
    children: list["BacklogTreeNode"] = Field(default_factory=list)


BacklogTreeNode.model_rebuild()
