import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.retro_entry import RetroCategory


class RetroEntryCreate(BaseModel):
    category: RetroCategory
    content: str = Field(min_length=1)


class RetroEntryOut(BaseModel):
    id: uuid.UUID
    sprint_id: uuid.UUID
    category: RetroCategory
    content: str
    created_by: uuid.UUID | None
    created_at: datetime

    model_config = {"from_attributes": True}
