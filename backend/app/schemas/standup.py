import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.standup_entry import StandupAuthor


class StandupEntryCreate(BaseModel):
    sprint_id: uuid.UUID | None = None
    content: str = Field(min_length=1)
    blockers: str | None = None


class StandupEntryOut(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    sprint_id: uuid.UUID | None
    author: StandupAuthor
    content: str
    blockers: str | None
    created_at: datetime

    model_config = {"from_attributes": True}
